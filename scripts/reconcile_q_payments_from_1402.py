"""Reconcile the main SATE system's payment ledger against the financial DB.

Source: an ad hoc export (``Q_PaymentsFrom1402.xlsx``) of every payment
recorded in the main SATE system since fiscal year 1402. Each row is matched
against ``payments.tracking_code``:

1. **Matched rows** (the payment already exists here): if this database is
   missing ``notification_letter_number`` and/or ``notification_date`` for
   that payment, backfill only the missing field(s) from the source row.
   Fields that are already populated here are never overwritten, and a
   field left blank in the source row is never used to backfill.
2. **Unmatched rows** (tracking code not found in ``payments`` at all): these
   are payments the executing institution funded directly out of its own
   resources, entirely outside the employer-managed budget pool. They are
   inserted into the separate ``trustee_payments`` table (see
   ``models/trustee_payments.py``) purely for contract-status reconciliation.
   They are intentionally kept out of ``payments`` and are never read by
   ``services.financial_engine.calculate_real_balance`` or any other
   employer balance/credit calculation.

Both phases are idempotent: re-running this script after fixing a data issue
will only touch rows that still need it, and will not create duplicate
``trustee_payments`` rows for tracking codes already imported.

Usage
-----
    python scripts/reconcile_q_payments_from_1402.py
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from core.date_helper import parse_strict_jalali_date  # noqa: E402
from models.contract import Contract  # noqa: E402
from models.payment import Payment  # noqa: E402
from models.trustee_payments import TrusteePayment  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("reconcile_q_payments_from_1402")

SOURCE_EXCEL_PATH = Path(r"C:\Users\Payam\Downloads\Q_PaymentsFrom1402.xlsx")
SOURCE_SHEET_NAME = "Q_PaymentsFrom1402"
TRUSTEE_EXPORT_PATH = PROJECT_ROOT / "data" / "Archive" / "trustee_payments_export.xlsx"
TRUSTEE_SOURCE_NOTE = (
    "پرداخت امانی: خارج از منابع کارفرما، از محل منابع موسسه مجری "
    "(وارد شده از Q_PaymentsFrom1402.xlsx)"
)


def _normalize_code(value: Any) -> Optional[str]:
    """Normalize a pandas numeric/tracking-code cell to a clean string."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text or None


def _clean_optional_text(value: Any) -> Optional[str]:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _clean_year(value: Any) -> Optional[int]:
    """Parse a fiscal-year cell into an integer, or ``None``."""
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _clean_amount(value: Any) -> Optional[int]:
    """Parse a Rial amount cell into a positive integer, or ``None``."""
    if pd.isna(value):
        return None
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return None
    return amount if amount > 0 else None


def _parse_notification_date(value: Any, tracking_code: str) -> Optional[date]:
    """Parse a Jalali notification-date cell, logging and skipping on failure."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    try:
        return parse_strict_jalali_date(cleaned)
    except (TypeError, ValueError) as exc:
        logger.warning(
            "Unparseable notification_date '%s' for tracking_code '%s': %s",
            cleaned,
            tracking_code,
            exc,
        )
        return None


def load_source_dataframe() -> pd.DataFrame:
    """Read and lightly normalize the source reconciliation workbook."""
    if not SOURCE_EXCEL_PATH.exists():
        raise FileNotFoundError(f"Source Excel file not found: {SOURCE_EXCEL_PATH}")

    dataframe = pd.read_excel(SOURCE_EXCEL_PATH, sheet_name=SOURCE_SHEET_NAME)
    logger.info("Loaded %d rows from %s", len(dataframe), SOURCE_EXCEL_PATH.name)

    dataframe["_payment_tc"] = dataframe["کد رهگیری پرداخت"].apply(_normalize_code)
    dataframe["_contract_tc"] = dataframe["کد رهگیری قرارداد"].apply(_normalize_code)

    before = len(dataframe)
    dataframe = dataframe.dropna(subset=["_payment_tc"])
    if len(dataframe) != before:
        logger.warning(
            "Dropped %d source rows with no payment tracking code.",
            before - len(dataframe),
        )

    duplicate_mask = dataframe["_payment_tc"].duplicated(keep="last")
    if duplicate_mask.any():
        logger.warning(
            "Dropped %d duplicate payment tracking codes (kept last occurrence).",
            int(duplicate_mask.sum()),
        )
        dataframe = dataframe[~duplicate_mask]

    return dataframe


def backfill_notification_fields(session: Session, dataframe: pd.DataFrame) -> dict[str, int]:
    """Fill missing notification_letter_number/notification_date on existing payments.

    Only touches a field that is currently ``NULL`` in the database *and*
    non-blank in the source row. Never overwrites an existing value.

    Returns:
        Counters: ``{"updated": n, "letter_filled": n, "date_filled": n}``.
    """
    tracking_codes = dataframe["_payment_tc"].tolist()
    existing_payments = {
        payment.tracking_code: payment
        for payment in session.query(Payment)
        .filter(Payment.tracking_code.in_(tracking_codes))
        .all()
    }

    counters = {"updated": 0, "letter_filled": 0, "date_filled": 0}

    for _, row in dataframe.iterrows():
        payment = existing_payments.get(row["_payment_tc"])
        if payment is None:
            continue

        row_changed = False
        source_letter = _clean_optional_text(row.get("شماره نامه ابلاغ"))
        if payment.notification_letter_number is None and source_letter is not None:
            payment.notification_letter_number = source_letter
            counters["letter_filled"] += 1
            row_changed = True

        if payment.notification_date is None:
            source_date = _parse_notification_date(
                row.get("تاریخ ابلاغ"), row["_payment_tc"]
            )
            if source_date is not None:
                payment.notification_date = source_date
                counters["date_filled"] += 1
                row_changed = True

        if row_changed:
            counters["updated"] += 1

    session.commit()
    return counters


def import_trustee_payments(session: Session, dataframe: pd.DataFrame) -> dict[str, int]:
    """Insert source rows whose tracking code is absent from ``payments``.

    Idempotent: tracking codes already present in ``trustee_payments`` are
    skipped rather than re-inserted or duplicated.

    Returns:
        Counters: ``{"candidates": n, "inserted": n, "skipped_existing": n,
        "unresolved_contract": n}``.
    """
    tracking_codes = dataframe["_payment_tc"].tolist()
    existing_payment_codes = {
        code
        for (code,) in session.query(Payment.tracking_code)
        .filter(Payment.tracking_code.in_(tracking_codes))
        .all()
    }
    already_imported = {
        code
        for (code,) in session.query(TrusteePayment.tracking_code).all()
    }

    contract_tracking_codes = dataframe["_contract_tc"].dropna().unique().tolist()
    contract_employer_map = {
        tracking_code: employer_code
        for tracking_code, employer_code in session.query(
            Contract.tracking_code, Contract.employer_code
        ).filter(Contract.tracking_code.in_(contract_tracking_codes))
    }

    counters = {
        "candidates": 0,
        "inserted": 0,
        "skipped_existing": 0,
        "unresolved_contract": 0,
    }
    new_records: list[TrusteePayment] = []

    for _, row in dataframe.iterrows():
        payment_tc = row["_payment_tc"]
        if payment_tc in existing_payment_codes:
            continue  # Already a real payment; handled by the backfill phase.

        counters["candidates"] += 1
        if payment_tc in already_imported:
            counters["skipped_existing"] += 1
            continue

        contract_tc = row["_contract_tc"]
        employer_code = contract_employer_map.get(contract_tc)
        if contract_tc is not None and employer_code is None:
            counters["unresolved_contract"] += 1

        amount = _clean_amount(row.get("مبلغ درخواستی(ریال)"))
        if amount is None:
            logger.warning(
                "Skipping trustee payment '%s': missing/non-positive amount.",
                payment_tc,
            )
            continue

        new_records.append(
            TrusteePayment(
                tracking_code=payment_tc,
                contract_tracking_code=contract_tc,
                employer_code=employer_code,
                amount=amount,
                payment_year=_clean_year(row.get("سال پرداخت")),
                notification_letter_number=_clean_optional_text(
                    row.get("شماره نامه ابلاغ")
                ),
                notification_date=_parse_notification_date(
                    row.get("تاریخ ابلاغ"), payment_tc
                ),
                source_note=TRUSTEE_SOURCE_NOTE,
                is_deleted=False,
            )
        )

    if new_records:
        session.add_all(new_records)
        session.commit()
    counters["inserted"] = len(new_records)
    return counters


def export_trustee_payments(session: Session) -> Path:
    """Export every active trustee payment to an Excel file for review."""
    import jdatetime

    rows = (
        session.query(TrusteePayment, Contract.title, Contract.employer_code)
        .outerjoin(
            Contract, TrusteePayment.contract_tracking_code == Contract.tracking_code
        )
        .filter(TrusteePayment.is_deleted == False)  # noqa: E712
        .order_by(TrusteePayment.tracking_code)
        .all()
    )

    def to_jalali(value: Optional[date]) -> Optional[str]:
        if value is None:
            return None
        return jdatetime.date.fromgregorian(date=value).strftime("%Y/%m/%d")

    records = [
        {
            "کد رهگیری پرداخت": tp.tracking_code,
            "کد رهگیری قرارداد": tp.contract_tracking_code,
            "عنوان قرارداد": contract_title,
            "کد کارفرما": tp.employer_code or contract_employer_code,
            "مبلغ (ریال)": int(tp.amount),
            "سال پرداخت": tp.payment_year,
            "شماره نامه ابلاغ": tp.notification_letter_number,
            "تاریخ ابلاغ (شمسی)": to_jalali(tp.notification_date),
            "توضیحات": tp.source_note,
        }
        for tp, contract_title, contract_employer_code in rows
    ]

    export_df = pd.DataFrame.from_records(records)
    TRUSTEE_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(TRUSTEE_EXPORT_PATH, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="پرداخت‌های امانی")

    logger.info("Exported %d trustee payments to %s", len(records), TRUSTEE_EXPORT_PATH)
    return TRUSTEE_EXPORT_PATH


def run_reconciliation() -> None:
    """Execute both reconciliation phases and print a final summary."""
    try:
        dataframe = load_source_dataframe()
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    session = SessionLocal()
    try:
        backfill_counters = backfill_notification_fields(session, dataframe)
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Backfill failed, transaction rolled back: %s", exc)
        session.close()
        return

    try:
        trustee_counters = import_trustee_payments(session, dataframe)
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Trustee payment import failed, transaction rolled back: %s", exc)
        session.close()
        return

    export_path = export_trustee_payments(session)
    session.close()

    print("\n" + "=" * 60)
    print("PAYMENT RECONCILIATION SUMMARY")
    print("=" * 60)
    print(f"Source rows processed:                {len(dataframe)}")
    print("--- Backfill (existing payments) ---")
    print(f"Payments updated:                     {backfill_counters['updated']}")
    print(f"  notification_letter_number filled:  {backfill_counters['letter_filled']}")
    print(f"  notification_date filled:           {backfill_counters['date_filled']}")
    print("--- Trustee payments (امانی) ---")
    print(f"Candidates (not in payments table):   {trustee_counters['candidates']}")
    print(f"Newly inserted:                       {trustee_counters['inserted']}")
    print(f"Already imported (skipped):           {trustee_counters['skipped_existing']}")
    print(f"Unresolved contract reference:        {trustee_counters['unresolved_contract']}")
    print(f"Exported to:                           {export_path}")
    print("=" * 60)


if __name__ == "__main__":
    run_reconciliation()
