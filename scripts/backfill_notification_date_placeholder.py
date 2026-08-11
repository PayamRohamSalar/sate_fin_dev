"""Backfill a placeholder notification_date for payments no source data covers.

After ``scripts/reconcile_q_payments_from_1402.py`` ran, 537 ``payments``
rows still had a ``NULL`` ``notification_date`` — either the tracking code
was absent from ``Q_PaymentsFrom1402.xlsx`` entirely, or it was present but
the source row's own ابلاغ columns were also blank. Since the contract
status dashboard needs *some* notification date to stop treating these
contracts as unresolved, this script fills a deliberate placeholder: **1
Shahrivar of the payment's own year** (e.g. a 1403 payment gets
``1403/06/01``), per explicit instruction. This is a proxy date for
dashboard resolution, not a claim that a real notification letter was issued
on that day — ``notification_date`` is set, but
``notification_letter_number`` is deliberately left ``NULL``, since no real
letter number exists to put there.

The same rule is applied to ``trustee_payments`` rows (currently none need
it — the reconciliation script already carried ``notification_date`` through
for every trustee row that had one in the source — but the logic exists here
so a future re-import with gaps is covered automatically).

Year source, in priority order, per row:
1. ``Q_PaymentsFrom1402.xlsx``'s "سال پرداخت" column, when the payment's
   tracking code is present in that file (even if its ابلاغ columns are
   blank).
2. This database's own ``payment_year`` column, when already populated
   (``payments`` and ``trustee_payments`` both have one).
3. For ``payments`` only: this database's own ``funding_year``, as a last
   resort (``trustee_payments`` has no equivalent field).

A row with no year available from any of these sources is skipped and
logged, not guessed.

Idempotent: only rows where ``notification_date IS NULL`` are touched, so
re-running after a partial failure or a data correction only affects rows
still missing the date.

Usage
-----
    python scripts/backfill_notification_date_placeholder.py
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import jdatetime
import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.contract import Contract  # noqa: E402,F401 (registers the FK target table)
from models.payment import Payment  # noqa: E402
from models.trustee_payments import TrusteePayment  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("backfill_notification_date_placeholder")

SOURCE_EXCEL_PATH = Path(r"C:\Users\Payam\Downloads\Q_PaymentsFrom1402.xlsx")
SOURCE_SHEET_NAME = "Q_PaymentsFrom1402"
PLACEHOLDER_JALALI_MONTH = 6  # Shahrivar
PLACEHOLDER_JALALI_DAY = 1


def _normalize_code(value) -> Optional[str]:
    """Normalize a pandas numeric/tracking-code cell to a clean string."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text or None


def _clean_year(value) -> Optional[int]:
    """Parse a fiscal-year cell into an integer, or ``None``."""
    if value is None or pd.isna(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def build_excel_year_map() -> dict[str, int]:
    """Build a ``{payment_tracking_code: سال پرداخت}`` map from the source file."""
    if not SOURCE_EXCEL_PATH.exists():
        raise FileNotFoundError(f"Source Excel file not found: {SOURCE_EXCEL_PATH}")

    dataframe = pd.read_excel(SOURCE_EXCEL_PATH, sheet_name=SOURCE_SHEET_NAME)
    dataframe["_payment_tc"] = dataframe["کد رهگیری پرداخت"].apply(_normalize_code)

    year_map: dict[str, int] = {}
    for _, row in dataframe.iterrows():
        tc = row["_payment_tc"]
        year = _clean_year(row.get("سال پرداخت"))
        if tc is not None and year is not None:
            year_map[tc] = year
    logger.info("Loaded %d payment-year mappings from source Excel.", len(year_map))
    return year_map


def placeholder_date_for_year(jalali_year: int) -> date:
    """Return the Gregorian date for 1 Shahrivar of the given Jalali year."""
    return jdatetime.date(
        jalali_year, PLACEHOLDER_JALALI_MONTH, PLACEHOLDER_JALALI_DAY
    ).togregorian()


def _new_counters() -> dict[str, int]:
    return {
        "from_excel_year": 0,
        "from_db_payment_year": 0,
        "from_db_funding_year": 0,
        "skipped_no_year": 0,
    }


def backfill_payments(session, excel_year_map: dict[str, int]) -> dict[str, int]:
    """Fill notification_date for every ``payments`` row still missing it."""
    counters = _new_counters()
    payments = (
        session.query(Payment).filter(Payment.notification_date.is_(None)).all()
    )
    logger.info("Found %d payments with notification_date still NULL.", len(payments))

    for payment in payments:
        year = excel_year_map.get(payment.tracking_code)
        source = "from_excel_year"
        if year is None:
            year = payment.payment_year
            source = "from_db_payment_year"
        if year is None:
            year = payment.funding_year
            source = "from_db_funding_year"

        if year is None:
            counters["skipped_no_year"] += 1
            logger.warning(
                "Skipping payment '%s': no year available from Excel, "
                "payment_year, or funding_year.",
                payment.tracking_code,
            )
            continue

        payment.notification_date = placeholder_date_for_year(year)
        counters[source] += 1

    return counters


def backfill_trustee_payments(session, excel_year_map: dict[str, int]) -> dict[str, int]:
    """Fill notification_date for every ``trustee_payments`` row still missing it."""
    counters = _new_counters()
    trustee_payments = (
        session.query(TrusteePayment)
        .filter(TrusteePayment.notification_date.is_(None))
        .all()
    )
    logger.info(
        "Found %d trustee payments with notification_date still NULL.",
        len(trustee_payments),
    )

    for trustee_payment in trustee_payments:
        year = excel_year_map.get(trustee_payment.tracking_code)
        source = "from_excel_year"
        if year is None:
            year = trustee_payment.payment_year
            source = "from_db_payment_year"

        if year is None:
            counters["skipped_no_year"] += 1
            logger.warning(
                "Skipping trustee payment '%s': no year available from "
                "Excel or payment_year.",
                trustee_payment.tracking_code,
            )
            continue

        trustee_payment.notification_date = placeholder_date_for_year(year)
        counters[source] += 1

    return counters


def _print_summary(title: str, counters: dict[str, int]) -> None:
    print(f"--- {title} ---")
    print(f"Filled from Excel 'سال پرداخت':         {counters['from_excel_year']}")
    print(f"Filled from DB payment_year:            {counters['from_db_payment_year']}")
    print(f"Filled from DB funding_year:             {counters['from_db_funding_year']}")
    print(f"Skipped (no year available anywhere):   {counters['skipped_no_year']}")


def run_backfill() -> None:
    """Fill notification_date for every payments/trustee_payments row missing it."""
    try:
        excel_year_map = build_excel_year_map()
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    session = SessionLocal()
    try:
        payment_counters = backfill_payments(session, excel_year_map)
        trustee_counters = backfill_trustee_payments(session, excel_year_map)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Backfill failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("NOTIFICATION_DATE PLACEHOLDER BACKFILL SUMMARY")
    print("=" * 60)
    _print_summary("payments", payment_counters)
    _print_summary("trustee_payments", trustee_counters)
    print("=" * 60)


if __name__ == "__main__":
    run_backfill()
