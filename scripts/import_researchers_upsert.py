"""Idempotent upsert ETL for the ``researchers`` table.

Loads researcher (فناور) records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (national_code)
DO UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Like
``scripts/import_universities_upsert.py``, this script never drops the
table and never performs an application-level "SELECT then INSERT/UPDATE"
check for the conflict target — PostgreSQL resolves the insert-vs-update
race atomically.

University resolution: the source file has no ``university_id`` column,
only a free-text institution name (``دانشگاه / محل خدمت``). Before
transforming rows, the full ``{name: national_id}`` mapping is loaded once
from the ``universities`` table (whitespace-stripped on both sides for
comparison) and used to resolve each row's ``university_id``. A row whose
institution name cannot be resolved is skipped and logged as a warning —
``researchers.university_id`` is a required foreign key, so there is no
safe default to fall back to.

Soft-delete interaction: if a ``national_code`` re-appears in the source
file after having been soft-deleted (``is_deleted = True``), the update
clause forces ``is_deleted = False``, restoring the record.

Usage
-----
    python scripts/import_researchers_upsert.py
"""

from __future__ import annotations

import io
import logging
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

from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.researchers import Researcher  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_researchers_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Researchers_Add_In.xlsx"

# Persian Excel header -> ORM/DB column name. The institution column is
# intentionally excluded here; it is resolved separately via the
# university name-to-id lookup (see resolve_university_id()).
COLUMN_MAPPING: dict[str, str] = {
    "کد ملی": "national_code",
    "کد رهگیری": "tracking_code",
    "نام نماینده": "first_name",
    "نام خانوادگی نماینده": "last_name",
    "تلفن همراه": "mobile",
    "ایمیل": "email",
    "درجه علمی": "academic_rank",
    "مدرک تحصیلی": "education_level",
    "نوع ثبت نام": "researcher_type",
    "وضعیت": "status",
}
UNIVERSITY_LOOKUP_COLUMN = "دانشگاه / محل خدمت"

NATIONAL_CODE_LENGTH = 10
DEFAULT_STATUS = "Active"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "tracking_code",
    "first_name",
    "last_name",
    "full_name",
    "mobile",
    "email",
    "academic_rank",
    "education_level",
    "researcher_type",
    "status",
    "university_id",
)


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"missing_university"`` or ``"invalid_data"``, used to
        route the row into the correct summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the researcher Excel workbook.

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


def _normalize_national_code(value: Any) -> str | None:
    """Normalize and zero-pad the primary-key column.

    Iranian national codes are 10 digits, but Excel frequently drops
    leading zeros when a numeric-looking ID column is stored as a number
    (and may also coerce it to a float, e.g. ``26746`` -> ``"26746.0"``).
    This strips the float artifact and left-pads with zeros to the
    standard 10-digit length.
    """
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    cleaned = _strip_numeric_artifact(cleaned)
    if not cleaned.isdigit():
        return cleaned  # Let the caller reject non-numeric codes explicitly.
    return cleaned.zfill(NATIONAL_CODE_LENGTH)


def build_university_lookup(session: Session) -> dict[str, str]:
    """Build a ``{stripped university name: national_id}`` lookup map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from whitespace-stripped, active university name to its
        ``national_id``. When two active universities share a stripped
        name, the last one read wins and a warning is logged.
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
            "missing_university",
            f"Blank '{UNIVERSITY_LOOKUP_COLUMN}' value.",
        )

    university_id = university_lookup.get(raw_name.strip())
    if university_id is None:
        raise RowSkipped(
            "missing_university",
            f"Institution '{raw_name}' not found among active universities.",
        )
    return university_id


def row_to_researcher_record(
    row: pd.Series,
    university_lookup: dict[str, str],
) -> dict[str, Any]:
    """Convert one Excel row into a sanitized ``researchers`` row dict.

    Args:
        row: A single row from the source DataFrame.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        A dict ready for the upsert statement.

    Raises:
        RowSkipped: If the row is missing a required field (national code,
            first name, last name) or its institution cannot be resolved.
    """
    national_code = _normalize_national_code(row.get("کد ملی"))
    if national_code is None or not national_code.isdigit():
        raise RowSkipped(
            "invalid_data", f"Missing or non-numeric national code: {national_code!r}."
        )
    if len(national_code) > NATIONAL_CODE_LENGTH:
        raise RowSkipped(
            "invalid_data",
            f"National code '{national_code}' exceeds "
            f"{NATIONAL_CODE_LENGTH} digits.",
        )

    first_name = _clean_optional_text(row.get("نام نماینده"))
    last_name = _clean_optional_text(row.get("نام خانوادگی نماینده"))
    if first_name is None or last_name is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing first/last name for national code '{national_code}'.",
        )

    # Resolve the required university FK before doing anything else; this
    # is the only condition classified as "missing university" for the
    # summary, keeping it distinct from other invalid-data skips.
    university_id = resolve_university_id(row, university_lookup)

    tracking_code = _clean_optional_text(row.get("کد رهگیری"))
    if tracking_code is not None:
        tracking_code = _strip_numeric_artifact(tracking_code)

    record: dict[str, Any] = {
        "national_code": national_code,
        "tracking_code": tracking_code,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}",
        "mobile": _mobile_as_text(row.get("تلفن همراه")),
        "email": _clean_optional_text(row.get("ایمیل")),
        "academic_rank": _clean_optional_text(row.get("درجه علمی")),
        "university_id": university_id,
        "education_level": _clean_optional_text(row.get("مدرک تحصیلی")),
        "researcher_type": _clean_optional_text(row.get("نوع ثبت نام")),
        "status": _clean_optional_text(row.get("وضعیت")) or DEFAULT_STATUS,
        "is_deleted": False,
    }
    return record


def _mobile_as_text(value: Any) -> str | None:
    """Clean a mobile-number cell, stripping any pandas float artifact."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def transform_dataframe(
    dataframe: pd.DataFrame,
    university_lookup: dict[str, str],
) -> tuple[list[dict[str, Any]], int, int]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``national_code`` values within the source file are
    collapsed to the last occurrence, since PostgreSQL rejects an
    ``ON CONFLICT`` batch that targets the same conflict key twice.

    Args:
        dataframe: The raw source worksheet.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        A tuple of (deduplicated records ready for upsert, rows skipped
        for a missing/unresolvable university, rows skipped for other
        invalid data).
    """
    records_by_national_code: dict[str, dict[str, Any]] = {}
    skipped_missing_university = 0
    skipped_invalid_data = 0

    for index, row in dataframe.iterrows():
        excel_row_number = index + 2  # 1-indexed plus header row offset.
        try:
            record = row_to_researcher_record(row, university_lookup)
        except RowSkipped as exc:
            if exc.reason == "missing_university":
                skipped_missing_university += 1
                logger.warning("Row %d skipped: %s", excel_row_number, exc)
            else:
                skipped_invalid_data += 1
                logger.warning("Row %d skipped: %s", excel_row_number, exc)
            continue

        records_by_national_code[record["national_code"]] = record

    return (
        list(records_by_national_code.values()),
        skipped_missing_university,
        skipped_invalid_data,
    )


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``national_code``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    insert_statement = pg_insert(Researcher).values(records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[Researcher.national_code],
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
        university_lookup = build_university_lookup(session)
    except SQLAlchemyError as exc:
        logger.error("Failed to load university lookup: %s", exc)
        session.close()
        return

    records, skipped_missing_university, skipped_invalid_data = transform_dataframe(
        dataframe, university_lookup
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
    print("RESEARCHER UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {len(dataframe)}")
    print(f"Skipped (missing/unmatched univ.): {skipped_missing_university}")
    print(f"Skipped (other invalid data):      {skipped_invalid_data}")
    print(f"Rows processed (upsert):           {processed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()
