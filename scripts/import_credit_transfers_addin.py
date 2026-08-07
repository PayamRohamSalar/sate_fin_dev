"""Application-level insert-ignore ETL for the ``credit_transfers`` table.

Loads new credit transfer records from an Excel workbook and appends them
to PostgreSQL one row at a time inside a single transaction. Unlike the
``*_upsert.py`` scripts in this directory, ``credit_transfers`` has no
business unique constraint — its only key is the auto-incrementing ``id``
— so a native ``INSERT ... ON CONFLICT`` upsert has no conflict target to
key off. Deduplication is therefore done in the application, against an
in-memory set of composite business keys built from the active rows
already in the table:

    (source_employer_code, destination_employer_code,
     contract_tracking_code, fiscal_year, amount)

A row whose composite key is already present — either in the database or
earlier in the same source file — is skipped as a duplicate rather than
inserted again.

Financial safety: before a row is accepted, the source employer's real
balance for the row's fiscal year is checked via
``services.financial_engine.calculate_real_balance`` and the row is
skipped if the balance cannot cover the transfer amount. Each accepted
row is ``session.flush()``-ed (not committed) immediately after
``session.add()`` so that a later row drawing from the *same* source
employer and fiscal year sees the reserved amount from earlier rows in
this run — without this, two individually-affordable rows in one batch
could jointly overdraw the source employer's balance. ``flush`` keeps
everything inside the same open transaction, so a single
``session.commit()`` at the very end (and a full ``session.rollback()``
on any exception) still governs the whole run, per the transaction-safety
requirement.

Usage
-----
    python scripts/import_credit_transfers_addin.py
"""

from __future__ import annotations

import io
import logging
import re
import sys
from pathlib import Path
from typing import Any

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
from models.contract import Contract  # noqa: E402
from models.employer import Employer  # noqa: E402
from models.transfer import CreditTransfer  # noqa: E402
from services.financial_engine import calculate_real_balance  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_credit_transfers_addin")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "CreditTransfer_Add_In.xlsx"

# Static Persian Excel header -> ORM/DB column name. The fiscal-year column
# is intentionally excluded here since its header embeds a year and varies
# between files (e.g. "انتقال از محل 1402سال مالی"); it is located
# separately via FISCAL_YEAR_COLUMN_HINT.
COLUMN_MAPPING: dict[str, str] = {
    "شماره طبقه بندی شرکت مبدأ": "source_employer_code",
    "شماره طبقه بندی شرکت مقصد": "destination_employer_code",
    "کارگزار قرارداد": "broker_name",
    "مبلغ انتقال (ریال)": "amount",
    "کد رهگیری قرارداد": "contract_tracking_code",
}

FISCAL_YEAR_COLUMN_HINT = re.compile("انتقال از محل")
# Fallback: a 4-digit Jalali-looking year (13xx/14xx) embedded in the
# column header itself, used only if the cell value under that column is
# blank for a given row.
YEAR_IN_HEADER_PATTERN = re.compile(r"(1[34]\d{2})")


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"invalid_data"``, ``"fk_error"``, ``"duplicate"``, or
        ``"insufficient_funds"``, used to route the row into the correct
        summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the credit transfer Excel workbook.

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


def find_fiscal_year_column(columns: list[str]) -> str:
    """Locate the dynamically-named fiscal-year column.

    Args:
        columns: The source DataFrame's column headers.

    Returns:
        The matching column name.

    Raises:
        ValueError: If no column header contains "انتقال از محل".
    """
    for column in columns:
        if FISCAL_YEAR_COLUMN_HINT.search(str(column)):
            return column
    raise ValueError(
        "No column containing 'انتقال از محل' found in the source file; "
        f"available columns: {list(columns)}"
    )


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
    """Normalize a classification/tracking code cell to a clean string."""
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
        cleaned = str(value).replace(",", "").replace(".", "").strip()
        if not cleaned:
            return None
        try:
            amount = int(float(cleaned))
        except ValueError:
            return None
    return amount if amount > 0 else None


def _resolve_fiscal_year(row: pd.Series, fiscal_year_column: str) -> int | None:
    """Resolve the row's fiscal year from its cell, falling back to the header.

    Args:
        row: A single row from the source DataFrame.
        fiscal_year_column: The column name located by
            :func:`find_fiscal_year_column`.

    Returns:
        The fiscal year as an integer, or ``None`` if it cannot be
        determined from either the cell value or the column header.
    """
    raw_value = row.get(fiscal_year_column)
    if not pd.isna(raw_value):
        try:
            return int(float(raw_value))
        except (TypeError, ValueError):
            pass

    header_match = YEAR_IN_HEADER_PATTERN.search(str(fiscal_year_column))
    if header_match:
        return int(header_match.group(1))
    return None


def build_active_employer_codes(session: Session) -> set[str]:
    """Load the set of active employer classification codes."""
    rows = (
        session.query(Employer.classification_code)
        .filter(Employer.is_deleted == False)  # noqa: E712
        .all()
    )
    codes = {code for (code,) in rows}
    logger.info("Loaded %d active employer codes.", len(codes))
    return codes


def build_active_contract_codes(session: Session) -> set[str]:
    """Load the set of active contract tracking codes."""
    rows = (
        session.query(Contract.tracking_code)
        .filter(Contract.is_deleted == False)  # noqa: E712
        .all()
    )
    codes = {code for (code,) in rows}
    logger.info("Loaded %d active contract tracking codes.", len(codes))
    return codes


def build_existing_transfer_keys(session: Session) -> set[tuple]:
    """Load composite business keys for every active credit transfer.

    Returns:
        A set of ``(source_employer_code, destination_employer_code,
        contract_tracking_code, fiscal_year, amount)`` tuples, with
        ``amount`` normalized to ``int`` to match the cleaned Excel values.
    """
    rows = (
        session.query(
            CreditTransfer.source_employer_code,
            CreditTransfer.destination_employer_code,
            CreditTransfer.contract_tracking_code,
            CreditTransfer.fiscal_year,
            CreditTransfer.amount,
        )
        .filter(CreditTransfer.is_deleted == False)  # noqa: E712
        .all()
    )
    keys = {
        (source, destination, contract_code, fiscal_year, int(amount))
        for source, destination, contract_code, fiscal_year, amount in rows
    }
    logger.info("Loaded %d existing credit transfer composite keys.", len(keys))
    return keys


def parse_row_fields(row: pd.Series, fiscal_year_column: str) -> dict[str, Any]:
    """Clean one Excel row into candidate ``credit_transfers`` field values.

    Args:
        row: A single row from the source DataFrame.
        fiscal_year_column: The dynamically-located fiscal-year column.

    Returns:
        A dict with cleaned ``source_employer_code``,
        ``destination_employer_code``, ``broker_name``, ``fiscal_year``,
        ``amount``, and ``contract_tracking_code`` values.

    Raises:
        RowSkipped: If any required field is missing or malformed.
    """
    source_employer_code = _normalize_code(row.get("شماره طبقه بندی شرکت مبدأ"))
    if source_employer_code is None:
        raise RowSkipped("invalid_data", "Missing source_employer_code.")

    destination_employer_code = _normalize_code(
        row.get("شماره طبقه بندی شرکت مقصد")
    )
    if destination_employer_code is None:
        raise RowSkipped("invalid_data", "Missing destination_employer_code.")

    contract_tracking_code = _normalize_code(row.get("کد رهگیری قرارداد"))
    if contract_tracking_code is None:
        raise RowSkipped("invalid_data", "Missing contract_tracking_code.")

    fiscal_year = _resolve_fiscal_year(row, fiscal_year_column)
    if fiscal_year is None:
        raise RowSkipped(
            "invalid_data",
            f"Could not determine fiscal_year from column "
            f"'{fiscal_year_column}' or its value.",
        )

    amount = _clean_amount(row.get("مبلغ انتقال (ریال)"))
    if amount is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing or non-positive amount: {row.get('مبلغ انتقال (ریال)')!r}.",
        )

    return {
        "source_employer_code": source_employer_code,
        "destination_employer_code": destination_employer_code,
        "broker_name": _clean_optional_text(row.get("کارگزار قرارداد")),
        "fiscal_year": fiscal_year,
        "amount": amount,
        "contract_tracking_code": contract_tracking_code,
    }


def validate_foreign_keys(
    fields: dict[str, Any],
    active_employer_codes: set[str],
    active_contract_codes: set[str],
) -> None:
    """Confirm every referenced employer/contract is active.

    Raises:
        RowSkipped: If the source employer, destination employer, or
            contract is not an active record.
    """
    if fields["source_employer_code"] not in active_employer_codes:
        raise RowSkipped(
            "fk_error",
            f"Source employer '{fields['source_employer_code']}' not found "
            "among active employers.",
        )
    if fields["destination_employer_code"] not in active_employer_codes:
        raise RowSkipped(
            "fk_error",
            f"Destination employer '{fields['destination_employer_code']}' "
            "not found among active employers.",
        )
    if fields["contract_tracking_code"] not in active_contract_codes:
        raise RowSkipped(
            "fk_error",
            f"Contract '{fields['contract_tracking_code']}' not found "
            "among active contracts.",
        )


def composite_key(fields: dict[str, Any]) -> tuple:
    """Build the composite business key used for insert-ignore deduplication."""
    return (
        fields["source_employer_code"],
        fields["destination_employer_code"],
        fields["contract_tracking_code"],
        fields["fiscal_year"],
        fields["amount"],
    )


def run_import() -> None:
    """Execute the end-to-end insert-ignore import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    try:
        fiscal_year_column = find_fiscal_year_column(list(dataframe.columns))
    except ValueError as exc:
        logger.error(str(exc))
        return
    logger.info("Resolved fiscal-year column: '%s'", fiscal_year_column)

    session = SessionLocal()

    skip_counts = {
        "invalid_data": 0,
        "fk_error": 0,
        "duplicate": 0,
        "insufficient_funds": 0,
    }
    inserted_count = 0
    total_rows = len(dataframe)

    try:
        active_employer_codes = build_active_employer_codes(session)
        active_contract_codes = build_active_contract_codes(session)
        existing_keys = build_existing_transfer_keys(session)

        for index, row in dataframe.iterrows():
            excel_row_number = index + 2  # 1-indexed plus header row offset.
            try:
                fields = parse_row_fields(row, fiscal_year_column)
                validate_foreign_keys(
                    fields, active_employer_codes, active_contract_codes
                )

                key = composite_key(fields)
                if key in existing_keys:
                    raise RowSkipped(
                        "duplicate",
                        f"Composite key {key} already exists.",
                    )

                current_balance = calculate_real_balance(
                    session,
                    fields["source_employer_code"],
                    fields["fiscal_year"],
                )
                if current_balance < fields["amount"]:
                    raise RowSkipped(
                        "insufficient_funds",
                        "INSUFFICIENT FUNDS for employer "
                        f"'{fields['source_employer_code']}' in fiscal year "
                        f"{fields['fiscal_year']}: current balance "
                        f"{current_balance:,.0f} Rials, requested transfer "
                        f"{fields['amount']:,.0f} Rials "
                        f"(deficit {fields['amount'] - current_balance:,.0f}).",
                    )

            except RowSkipped as exc:
                skip_counts[exc.reason] += 1
                logger.warning("Row %d skipped: %s", excel_row_number, exc)
                continue

            transfer = CreditTransfer(
                source_employer_code=fields["source_employer_code"],
                destination_employer_code=fields["destination_employer_code"],
                broker_name=fields["broker_name"],
                fiscal_year=fields["fiscal_year"],
                amount=fields["amount"],
                contract_tracking_code=fields["contract_tracking_code"],
                is_deleted=False,
            )
            session.add(transfer)
            # Flush (not commit) so a later row against the same source
            # employer/fiscal year sees this reserved amount in its own
            # balance check, and so an in-file duplicate of this exact row
            # is caught by the composite-key set below.
            session.flush()
            existing_keys.add(key)
            inserted_count += 1
            logger.info(
                "Row %d accepted: %s -> %s, contract %s, fiscal_year %s, "
                "amount %s Rials.",
                excel_row_number,
                fields["source_employer_code"],
                fields["destination_employer_code"],
                fields["contract_tracking_code"],
                fields["fiscal_year"],
                f"{fields['amount']:,.0f}",
            )

        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Import failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("CREDIT TRANSFER APPEND SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {total_rows}")
    print(f"Inserted:                         {inserted_count}")
    print(f"Skipped (duplicate):               {skip_counts['duplicate']}")
    print(f"Skipped (FK error):                {skip_counts['fk_error']}")
    print(f"Skipped (insufficient funds):      {skip_counts['insufficient_funds']}")
    print(f"Skipped (other invalid data):       {skip_counts['invalid_data']}")
    print("=" * 60)


if __name__ == "__main__":
    run_import()
