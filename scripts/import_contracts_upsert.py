"""Idempotent upsert ETL for the ``contracts`` table.

Loads contract records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (tracking_code)
DO UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Like
``scripts/import_universities_upsert.py`` and
``scripts/import_researchers_upsert.py``, this script never drops the
table and never performs an application-level "SELECT then INSERT/UPDATE"
check for the conflict target — PostgreSQL resolves the insert-vs-update
race atomically.

Triple FK resolution: the source file has no ``employer_code``,
``university_id``, or ``researcher_id`` columns — only free-text names for
Employer (``متقاضی``), University (``دانشگاه``), and Researcher
(``فناور``). Three lookups are built once from the database before any row
is processed:

* ``employer_lookup``  : ``{name.strip(): (classification_code, employer_type)}``
* ``university_lookup``: ``{name.strip(): national_id}``
* ``researcher_lookup`` : ``{(full_name.strip(), university_id): national_code}``

The researcher lookup is keyed on ``(full_name, university_id)`` rather
than name alone, since two researchers can share a name across different
universities; resolving the researcher therefore requires the row's
university to have resolved first.

Business rule (see ``models/employer.py`` / ``api/v1/endpoints/contracts.py``):
contracts may only be registered under a ``Mother`` or ``Independent``
employer, never a ``Subsidiary``. This is why ``employer_lookup`` carries
the employer type alongside its code — a row whose employer resolves by
name but is a ``Subsidiary`` is skipped exactly like an unresolved
employer, since neither case yields a contractable employer.

Soft-delete interaction: if a ``tracking_code`` re-appears in the source
file after having been soft-deleted (``is_deleted = True``), the update
clause forces ``is_deleted = False``, restoring the record.

Usage
-----
    python scripts/import_contracts_upsert.py
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
from models.employer import Employer  # noqa: E402
from models.researchers import Researcher  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_contracts_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Contracts_Add_In.xlsx"

EMPLOYER_LOOKUP_COLUMN = "متقاضی"
UNIVERSITY_LOOKUP_COLUMN = "دانشگاه"
RESEARCHER_LOOKUP_COLUMN = "فناور"

# Per the system's immutable business rule: contracts may only be
# registered under a Mother or Independent employer, never a Subsidiary.
ALLOWED_CONTRACT_EMPLOYER_TYPES = {"Mother", "Independent"}

DEFAULT_STATUS = "Active"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "employer_code",
    "university_id",
    "researcher_id",
    "proposal_id",
    "contract_number",
    "contract_date",
    "total_amount",
    "title",
    "duration_months",
    "status",
)


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"missing_employer"``, ``"missing_university"``,
        ``"missing_researcher"``, ``"bad_date"``, or ``"invalid_data"``,
        used to route the row into the correct summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the contract Excel workbook.

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


def _normalize_tracking_code(value: Any) -> str | None:
    """Normalize the primary-key column, stripping pandas' float artifacts."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def build_employer_lookup(session: Session) -> dict[str, tuple[str, str]]:
    """Build a ``{stripped employer name: (classification_code, employer_type)}`` map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from whitespace-stripped, active employer name to its
        ``(classification_code, employer_type)``. When two active
        employers share a stripped name, the last one read wins and a
        warning is logged.
    """
    rows = (
        session.query(
            Employer.name, Employer.classification_code, Employer.employer_type
        )
        .filter(Employer.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[str, tuple[str, str]] = {}
    for name, classification_code, employer_type in rows:
        if name is None:
            continue
        key = name.strip()
        if key in lookup and lookup[key][0] != classification_code:
            logger.warning(
                "Duplicate employer name '%s' maps to multiple "
                "classification_code values; using the last one seen.",
                key,
            )
        lookup[key] = (classification_code, employer_type)

    logger.info("Built employer lookup with %d entries.", len(lookup))
    return lookup


def build_university_lookup(session: Session) -> dict[str, str]:
    """Build a ``{stripped university name: national_id}`` lookup map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from whitespace-stripped, active university name to its
        ``national_id``.
    """
    rows = (
        session.query(University.name, University.national_id)
        .filter(University.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[str, str] = {}
    for name, national_id in rows:
        if name is None:
            continue
        key = name.strip()
        if key in lookup and lookup[key] != national_id:
            logger.warning(
                "Duplicate university name '%s' maps to multiple "
                "national_id values; using the last one seen.",
                key,
            )
        lookup[key] = national_id

    logger.info("Built university lookup with %d entries.", len(lookup))
    return lookup


def build_researcher_lookup(session: Session) -> dict[tuple[str, str], str]:
    """Build a ``{(full_name, university_id): national_code}`` lookup map.

    The composite key prevents cross-matching two different researchers
    who happen to share a full name at different universities.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from ``(stripped full_name, university_id)`` to the
        active researcher's ``national_code``.
    """
    rows = (
        session.query(
            Researcher.full_name, Researcher.university_id, Researcher.national_code
        )
        .filter(Researcher.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[tuple[str, str], str] = {}
    for full_name, university_id, national_code in rows:
        if full_name is None:
            continue
        key = (full_name.strip(), university_id)
        lookup[key] = national_code

    logger.info("Built researcher lookup with %d entries.", len(lookup))
    return lookup


def resolve_employer_code(
    row: pd.Series,
    employer_lookup: dict[str, tuple[str, str]],
) -> str:
    """Resolve a row's free-text employer name to a ``classification_code``.

    Args:
        row: A single row from the source DataFrame.
        employer_lookup: Mapping built by :func:`build_employer_lookup`.

    Returns:
        The matching employer's ``classification_code``.

    Raises:
        RowSkipped: If the employer name is blank, does not match any
            active employer, or resolves to a ``Subsidiary`` employer
            (ineligible to hold a contract).
    """
    raw_name = _clean_optional_text(row.get(EMPLOYER_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_employer", f"Blank '{EMPLOYER_LOOKUP_COLUMN}' value."
        )

    resolved = employer_lookup.get(raw_name.strip())
    if resolved is None:
        raise RowSkipped(
            "missing_employer",
            f"Employer '{raw_name}' not found among active employers.",
        )

    classification_code, employer_type = resolved
    if employer_type not in ALLOWED_CONTRACT_EMPLOYER_TYPES:
        raise RowSkipped(
            "missing_employer",
            f"Employer '{raw_name}' is a '{employer_type}' employer; only "
            f"{sorted(ALLOWED_CONTRACT_EMPLOYER_TYPES)} may hold contracts.",
        )
    return classification_code


def resolve_university_id(
    row: pd.Series,
    university_lookup: dict[str, str],
) -> str:
    """Resolve a row's free-text institution name to a ``university_id``.

    Args:
        row: A single row from the source DataFrame.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        The matching university's ``national_id``.

    Raises:
        RowSkipped: If the institution name is blank or does not match any
            active university.
    """
    raw_name = _clean_optional_text(row.get(UNIVERSITY_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_university", f"Blank '{UNIVERSITY_LOOKUP_COLUMN}' value."
        )

    university_id = university_lookup.get(raw_name.strip())
    if university_id is None:
        raise RowSkipped(
            "missing_university",
            f"Institution '{raw_name}' not found among active universities.",
        )
    return university_id


def resolve_researcher_id(
    row: pd.Series,
    university_id: str,
    researcher_lookup: dict[tuple[str, str], str],
) -> str:
    """Resolve a row's free-text researcher name to a ``national_code``.

    Args:
        row: A single row from the source DataFrame.
        university_id: The row's already-resolved ``university_id``, used
            as the second half of the composite lookup key.
        researcher_lookup: Mapping built by :func:`build_researcher_lookup`.

    Returns:
        The matching researcher's ``national_code``.

    Raises:
        RowSkipped: If the researcher name is blank or does not match any
            active researcher at the resolved university.
    """
    raw_name = _clean_optional_text(row.get(RESEARCHER_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_researcher", f"Blank '{RESEARCHER_LOOKUP_COLUMN}' value."
        )

    national_code = researcher_lookup.get((raw_name.strip(), university_id))
    if national_code is None:
        raise RowSkipped(
            "missing_researcher",
            f"Researcher '{raw_name}' not found at university_id "
            f"'{university_id}'.",
        )
    return national_code


def parse_contract_date(row: pd.Series) -> date | None:
    """Strictly parse the Jalali contract-date column.

    Args:
        row: A single row from the source DataFrame.

    Returns:
        The equivalent Gregorian date, or ``None`` if the source cell is
        blank (``contract_date`` is a nullable column).

    Raises:
        RowSkipped: If the cell holds a non-blank value that fails strict
            Jalali calendar validation.
    """
    raw_value = row.get("تاریخ قرارداد")
    if pd.isna(raw_value):
        return None

    try:
        return parse_strict_jalali_date(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise RowSkipped(
            "bad_date", f"Invalid Jalali contract date '{raw_value}': {exc}"
        ) from exc


def _clean_total_amount(row: pd.Series) -> int:
    """Parse the contract amount into a whole-Rial integer.

    Raises:
        RowSkipped: If the amount is blank or not a valid number.
    """
    raw_value = row.get("مبلغ قرارداد(ریال)")
    if pd.isna(raw_value):
        raise RowSkipped("invalid_data", "Missing total_amount.")
    try:
        return int(float(raw_value))
    except (TypeError, ValueError) as exc:
        raise RowSkipped(
            "invalid_data", f"Non-numeric total_amount '{raw_value}': {exc}"
        ) from exc


def _clean_duration_months(row: pd.Series) -> int | None:
    """Parse the optional contract duration into an integer month count."""
    raw_value = row.get("مدت زمان اجرا (ماه)")
    if pd.isna(raw_value):
        return None
    try:
        return int(float(raw_value))
    except (TypeError, ValueError):
        return None


def row_to_contract_record(
    row: pd.Series,
    employer_lookup: dict[str, tuple[str, str]],
    university_lookup: dict[str, str],
    researcher_lookup: dict[tuple[str, str], str],
) -> dict[str, Any]:
    """Convert one Excel row into a sanitized ``contracts`` row dict.

    Args:
        row: A single row from the source DataFrame.
        employer_lookup: Mapping built by :func:`build_employer_lookup`.
        university_lookup: Mapping built by :func:`build_university_lookup`.
        researcher_lookup: Mapping built by :func:`build_researcher_lookup`.

    Returns:
        A dict ready for the upsert statement.

    Raises:
        RowSkipped: If the row is missing a required field, its employer,
            university, or researcher cannot be resolved, or its contract
            date fails strict Jalali validation.
    """
    tracking_code = _normalize_tracking_code(row.get("کد رهگیری"))
    if tracking_code is None:
        raise RowSkipped("invalid_data", "Missing tracking_code.")

    title = _clean_optional_text(row.get("عنوان قرارداد"))
    if title is None:
        raise RowSkipped(
            "invalid_data", f"Missing title for tracking_code '{tracking_code}'."
        )

    # Resolution order matches the spec: employer, then university, then
    # researcher (which depends on the resolved university_id).
    employer_code = resolve_employer_code(row, employer_lookup)
    university_id = resolve_university_id(row, university_lookup)
    researcher_id = resolve_researcher_id(row, university_id, researcher_lookup)

    contract_date = parse_contract_date(row)
    total_amount = _clean_total_amount(row)
    duration_months = _clean_duration_months(row)

    proposal_id = _clean_optional_text(row.get("شناسه پیشنهاده"))
    if proposal_id is not None:
        proposal_id = _strip_numeric_artifact(proposal_id)

    record: dict[str, Any] = {
        "tracking_code": tracking_code,
        "employer_code": employer_code,
        "university_id": university_id,
        "researcher_id": researcher_id,
        "proposal_id": proposal_id,
        "contract_number": _clean_optional_text(row.get("شماره قرارداد")),
        "contract_date": contract_date,
        "total_amount": total_amount,
        "title": title,
        "duration_months": duration_months,
        "status": _clean_optional_text(row.get("وضعیت")) or DEFAULT_STATUS,
        "is_deleted": False,
    }
    return record


def transform_dataframe(
    dataframe: pd.DataFrame,
    employer_lookup: dict[str, tuple[str, str]],
    university_lookup: dict[str, str],
    researcher_lookup: dict[tuple[str, str], str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``tracking_code`` values within the source file are
    collapsed to the last occurrence, since PostgreSQL rejects an
    ``ON CONFLICT`` batch that targets the same conflict key twice.

    Args:
        dataframe: The raw source worksheet.
        employer_lookup: Mapping built by :func:`build_employer_lookup`.
        university_lookup: Mapping built by :func:`build_university_lookup`.
        researcher_lookup: Mapping built by :func:`build_researcher_lookup`.

    Returns:
        A tuple of (deduplicated records ready for upsert, skip counters
        keyed by reason).
    """
    records_by_tracking_code: dict[str, dict[str, Any]] = {}
    skip_counts = {
        "missing_employer": 0,
        "missing_university": 0,
        "missing_researcher": 0,
        "bad_date": 0,
        "invalid_data": 0,
    }

    for index, row in dataframe.iterrows():
        excel_row_number = index + 2  # 1-indexed plus header row offset.
        try:
            record = row_to_contract_record(
                row, employer_lookup, university_lookup, researcher_lookup
            )
        except RowSkipped as exc:
            skip_counts[exc.reason] += 1
            logger.warning("Row %d skipped: %s", excel_row_number, exc)
            continue

        records_by_tracking_code[record["tracking_code"]] = record

    return list(records_by_tracking_code.values()), skip_counts


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``tracking_code``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    insert_statement = pg_insert(Contract).values(records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[Contract.tracking_code],
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
        employer_lookup = build_employer_lookup(session)
        university_lookup = build_university_lookup(session)
        researcher_lookup = build_researcher_lookup(session)
    except SQLAlchemyError as exc:
        logger.error("Failed to build lookup tables: %s", exc)
        session.close()
        return

    records, skip_counts = transform_dataframe(
        dataframe, employer_lookup, university_lookup, researcher_lookup
    )

    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        session.close()
        return

    statement = build_upsert_statement(records)

    try:
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
    print("CONTRACT UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {len(dataframe)}")
    print(f"Skipped (missing employer):        {skip_counts['missing_employer']}")
    print(f"Skipped (missing university):      {skip_counts['missing_university']}")
    print(f"Skipped (missing researcher):      {skip_counts['missing_researcher']}")
    print(f"Skipped (bad contract date):       {skip_counts['bad_date']}")
    print(f"Skipped (other invalid data):      {skip_counts['invalid_data']}")
    print(f"Rows processed (upsert):           {processed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()
