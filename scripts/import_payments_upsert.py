"""Idempotent upsert ETL for the ``payments`` table.

Loads payment records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (tracking_code)
DO UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Like
the other ``*_upsert.py`` scripts in this directory, this script never
drops the table and never performs an application-level "SELECT then
INSERT/UPDATE" check for the conflict target — PostgreSQL resolves the
insert-vs-update race atomically.

Missing NOT NULL columns: the source file has no ``payment_date``,
``execution_year``, or ``payment_type`` columns, all of which are
``nullable=False`` on ``Payment``. Per the task's fallback rules:

* ``payment_date``  <- the row's parsed ``notification_date`` (``تاریخ
  ابلاغ``); if that fails to parse, the row is skipped entirely, since
  there is no other date to fall back to.
* ``execution_year`` <- ``int(funding_year)`` (``پرداخت از محل سال مالی``).
* ``payment_type``   <- the fixed placeholder ``"نامشخص"``.

Financial warning (FR-20): before a row is accepted, its projected balance
is checked via ``services.financial_engine.calculate_real_balance``, but a
negative projection only logs a warning and increments a counter — it
never skips the row, matching the system-wide FR-20 rule that negative
balances warn but do not block. Balances are tracked as a running,
in-memory projection per ``(employer_code, funding_year)`` across the
whole batch (mirroring ``api/v1/endpoints/payments.py``'s
``bulk_submit_payments``), so a second payment in this same file against
the same employer and funding year is checked against the balance *after*
the first payment's amount has been provisionally subtracted, not against
the stale pre-batch database balance.

Usage
-----
    python scripts/import_payments_upsert.py
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from core.date_helper import parse_strict_jalali_date  # noqa: E402
from models.contract import Contract  # noqa: E402
from models.payment import Payment  # noqa: E402
from services.financial_engine import calculate_real_balance  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_payments_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Payments_Add_In.xlsx"

PAYMENT_TYPE_PLACEHOLDER = "نامشخص"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "contract_tracking_code",
    "series",
    "amount",
    "notification_letter_number",
    "notification_date",
    "payment_year",
    "funding_year",
    "payment_date",
    "execution_year",
    "payment_type",
)


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"missing_fk"``, ``"bad_date"``, or ``"invalid_data"``,
        used to route the row into the correct summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the payments Excel workbook.

    Returns:
        The raw, unmodified worksheet contents.

    Raises:
        FileNotFoundError: If ``excel_path`` does not exist.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    dataframe = pd.read_excel(excel_path, engine="openpyxl")
    logger.info("Loaded %d rows from %s", len(dataframe), excel_path.name)
    return dataframe


def _clean_optional_text(value: Any) -> str | None:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _strip_numeric_artifact(value: str) -> str:
    """Trim pandas' trailing ``.0`` float artifact from a numeric-looking ID."""
    if value.endswith(".0"):
        return value[:-2]
    return value


def _normalize_code(value: Any) -> str | None:
    """Normalize a tracking-code cell to a clean string."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def _clean_amount(value: Any) -> int | None:
    """Parse a Rial amount cell into a positive integer, or ``None``."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        amount = int(value)
    else:
        cleaned = str(value).replace(",", "").strip()
        if not cleaned:
            return None
        try:
            amount = int(float(cleaned))
        except ValueError:
            return None
    return amount if amount > 0 else None


def _clean_year(value: Any) -> int | None:
    """Parse a fiscal-year cell into an integer, or ``None``."""
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def build_valid_contracts(session: Session) -> dict[str, str]:
    """Build a ``{contract_tracking_code: employer_code}`` lookup map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from every active contract's tracking code to its
        linked employer's classification code.
    """
    rows = (
        session.query(Contract.tracking_code, Contract.employer_code)
        .filter(Contract.is_deleted == False)  # noqa: E712
        .all()
    )
    lookup = {tracking_code: employer_code for tracking_code, employer_code in rows}
    logger.info("Loaded %d active contract tracking codes.", len(lookup))
    return lookup


def build_existing_payment_amounts(session: Session) -> dict[str, float]:
    """Build a ``{tracking_code: amount}`` map of every active payment.

    Used by :func:`apply_balance_warnings` to avoid double-counting a
    payment that already exists in the database: ``calculate_real_balance``
    already reflects committed payments, so re-subtracting an existing
    row's amount on every re-run (an ``ON CONFLICT DO UPDATE``, not a new
    insert) would understate the balance more each time the script runs
    against unchanged data.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from every active payment's tracking code to its current
        ``amount`` (as ``float``, to match ``calculate_real_balance``'s
        return type).
    """
    rows = (
        session.query(Payment.tracking_code, Payment.amount)
        .filter(Payment.is_deleted == False)  # noqa: E712
        .all()
    )
    return {tracking_code: float(amount) for tracking_code, amount in rows}


def parse_row_fields(row: pd.Series, valid_contracts: dict[str, str]) -> dict[str, Any]:
    """Clean and validate one Excel row into candidate ``payments`` fields.

    Args:
        row: A single row from the source DataFrame.
        valid_contracts: Mapping built by :func:`build_valid_contracts`.

    Returns:
        A dict with every cleaned field plus the resolved ``employer_code``
        (kept alongside the record for the FR-20 balance check, not itself
        a ``payments`` column).

    Raises:
        RowSkipped: If the contract reference is missing/invalid, the
            notification date cannot be parsed, or another required field
            is missing/malformed.
    """
    tracking_code = _normalize_code(row.get("کد رهگیری پرداخت"))
    if tracking_code is None:
        raise RowSkipped("invalid_data", "Missing tracking_code.")

    contract_tracking_code = _normalize_code(row.get("کد رهگیری"))
    if contract_tracking_code is None:
        raise RowSkipped(
            "missing_fk",
            f"Missing contract_tracking_code for payment '{tracking_code}'.",
        )
    employer_code = valid_contracts.get(contract_tracking_code)
    if employer_code is None:
        raise RowSkipped(
            "missing_fk",
            f"Contract '{contract_tracking_code}' not found among active "
            "contracts.",
        )

    raw_notification_date = row.get("تاریخ ابلاغ")
    if pd.isna(raw_notification_date):
        raise RowSkipped(
            "bad_date",
            f"Missing notification_date for payment '{tracking_code}'.",
        )
    try:
        notification_date: date = parse_strict_jalali_date(str(raw_notification_date))
    except (TypeError, ValueError) as exc:
        raise RowSkipped(
            "bad_date",
            f"Invalid Jalali notification_date "
            f"'{raw_notification_date}' for payment '{tracking_code}': {exc}",
        ) from exc

    amount = _clean_amount(row.get("مبلغ پرداختی(ریال)"))
    if amount is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing or non-positive amount for payment '{tracking_code}'.",
        )

    funding_year = _clean_year(row.get("پرداخت از محل سال مالی"))
    if funding_year is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing or non-numeric funding_year for payment "
            f"'{tracking_code}'.",
        )

    payment_year = _clean_year(row.get("سال پرداخت"))

    return {
        "tracking_code": tracking_code,
        "contract_tracking_code": contract_tracking_code,
        "series": _clean_optional_text(row.get("سری پرداخت")),
        "amount": amount,
        "notification_letter_number": _clean_optional_text(
            row.get("شماره نامه ابلاغ")
        ),
        "notification_date": notification_date,
        "payment_year": payment_year,
        "funding_year": funding_year,
        # Fallbacks for columns absent from the source file but NOT NULL
        # on the model.
        "payment_date": notification_date,
        "execution_year": funding_year,
        "payment_type": PAYMENT_TYPE_PLACEHOLDER,
        "is_deleted": False,
        # Not a payments column; carried through for the FR-20 check below.
        "_employer_code": employer_code,
    }


def transform_dataframe(
    dataframe: pd.DataFrame,
    valid_contracts: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``tracking_code`` values within the source file are
    collapsed to the last occurrence, since PostgreSQL rejects an
    ``ON CONFLICT`` batch that targets the same conflict key twice.

    Args:
        dataframe: The raw source worksheet.
        valid_contracts: Mapping built by :func:`build_valid_contracts`.

    Returns:
        A tuple of (deduplicated records ready for upsert, skip counters
        keyed by reason).
    """
    records_by_tracking_code: dict[str, dict[str, Any]] = {}
    skip_counts = {"missing_fk": 0, "bad_date": 0, "invalid_data": 0}

    for index, row in dataframe.iterrows():
        excel_row_number = index + 2  # 1-indexed plus header row offset.
        try:
            record = parse_row_fields(row, valid_contracts)
        except RowSkipped as exc:
            skip_counts[exc.reason] += 1
            logger.warning("Row %d skipped: %s", excel_row_number, exc)
            continue

        records_by_tracking_code[record["tracking_code"]] = record

    return list(records_by_tracking_code.values()), skip_counts


def apply_balance_warnings(
    session: Session,
    records: list[dict[str, Any]],
    existing_payment_amounts: dict[str, float],
) -> list[str]:
    """Project each payment's impact on its employer's balance (FR-20).

    A negative projected balance never removes the row from ``records`` —
    it only produces a warning message and is logged. Balances are tracked
    as a running total per ``(employer_code, funding_year)`` across
    ``records`` in order, so multiple payments in this file against the
    same employer/year are checked cumulatively rather than each against
    the stale pre-batch database balance.

    ``calculate_real_balance`` already sums every active payment in the
    database, including ones this same run is about to *update* (not
    insert) via ``ON CONFLICT``. Before subtracting such a row's amount,
    its previously-committed amount is added back first, so re-running
    this script against unchanged data doesn't double-count an existing
    payment and manufacture a growing deficit on every run.

    Args:
        session: Active SQLAlchemy session.
        records: Sanitized rows produced by :func:`transform_dataframe`.
        existing_payment_amounts: Mapping built by
            :func:`build_existing_payment_amounts`.

    Returns:
        Human-readable warning messages, one per payment that projects a
        negative balance.
    """
    running_balances: dict[tuple[str, int], float] = {}
    warnings: list[str] = []

    for record in records:
        employer_code = record["_employer_code"]
        funding_year = record["funding_year"]
        balance_key = (employer_code, funding_year)

        if balance_key not in running_balances:
            running_balances[balance_key] = calculate_real_balance(
                session, employer_code, funding_year
            )

        # Undo this row's own prior contribution (if any) before applying
        # its new amount, so an update of an unchanged existing row nets
        # to zero instead of being subtracted a second time.
        running_balances[balance_key] += existing_payment_amounts.get(
            record["tracking_code"], 0.0
        )
        running_balances[balance_key] -= record["amount"]
        if running_balances[balance_key] < 0:
            message = (
                "FR-20 WARNING: payment "
                f"'{record['tracking_code']}' projects a negative balance "
                f"for employer '{employer_code}', funding year "
                f"{funding_year}: {running_balances[balance_key]:,.0f} "
                "Rials (deficit "
                f"{-running_balances[balance_key]:,.0f} Rials)."
            )
            warnings.append(message)
            logger.warning(message)

    return warnings


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``tracking_code``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.
            The internal ``_employer_code`` key is stripped before the
            statement is built, since it is not a ``payments`` column.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    payment_columns = {
        column.name for column in Payment.__table__.columns
    }
    clean_records = [
        {key: value for key, value in record.items() if key in payment_columns}
        for record in records
    ]

    insert_statement = pg_insert(Payment).values(clean_records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[Payment.tracking_code],
        set_=update_columns,
    )


def run_upsert_import() -> None:
    """Execute the end-to-end upsert import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    session = SessionLocal()
    try:
        valid_contracts = build_valid_contracts(session)
        existing_payment_amounts = build_existing_payment_amounts(session)
    except SQLAlchemyError as exc:
        logger.error("Failed to load lookup data: %s", exc)
        session.close()
        return

    records, skip_counts = transform_dataframe(dataframe, valid_contracts)

    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        session.close()
        return

    try:
        warnings = apply_balance_warnings(session, records, existing_payment_amounts)
        statement = build_upsert_statement(records)
        result = session.execute(statement)
        session.commit()
        processed_count = result.rowcount
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Upsert failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("PAYMENT UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {len(dataframe)}")
    print(f"Skipped (missing/invalid FK):      {skip_counts['missing_fk']}")
    print(f"Skipped (invalid date):            {skip_counts['bad_date']}")
    print(f"Skipped (other invalid data):      {skip_counts['invalid_data']}")
    print(f"Rows processed (upsert):           {processed_count}")
    print(f"FR-20 negative-balance warnings:   {len(warnings)}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()
