"""Idempotent upsert ETL for the ``universities`` table.

Loads university records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (national_id) DO
UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Unlike
``scripts/import_universities.py`` (the original truncate/reload loader),
this script never drops the table and never performs an application-level
"SELECT then INSERT/UPDATE" check — the conflict resolution happens
atomically inside PostgreSQL, which avoids the time-of-check to
time-of-use race that a Python-side existence check would introduce under
concurrent runs.

Soft-delete interaction: if a ``national_id`` re-appears in the source file
after having been soft-deleted (``is_deleted = True``), the update clause
forces ``is_deleted = False``, restoring the record instead of leaving it
hidden.

Usage
-----
    python scripts/import_universities_upsert.py
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

from core.database import SessionLocal  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_universities_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Universities_Add_In.xlsx"

# Persian Excel header -> ORM/DB column name.
COLUMN_MAPPING: dict[str, str] = {
    "کد رهگیری": "tracking_code",
    "شناسه ملی موسسه": "national_id",
    "نام موسسه": "name",
    "نوع موسسه": "university_type",
    "استان": "province",
    "شهر": "city",
    "آدرس": "address",
    "وضعیت": "status",
}

# Safe defaults for NOT NULL columns that may be blank in the source file.
DEFAULT_PROVINCE = "نامشخص"
DEFAULT_UNIVERSITY_TYPE = "نامشخص"
DEFAULT_STATUS = "Active"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "tracking_code",
    "name",
    "province",
    "university_type",
    "status",
    "city",
    "address",
)


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the university Excel workbook.

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


def _normalize_national_id(value: Any) -> str | None:
    """Normalize the primary-key column, stripping pandas' float artifacts.

    Numeric ID columns read from Excel are frequently coerced to floats
    (e.g. ``10102894887`` becomes ``"10102894887.0"``); this trims a
    trailing ``.0`` so the value matches previously imported string IDs.
    """
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    if cleaned.endswith(".0"):
        cleaned = cleaned[:-2]
    return cleaned


def row_to_university_record(row: pd.Series) -> dict[str, Any] | None:
    """Convert one Excel row into a sanitized ``universities`` row dict.

    Args:
        row: A single row from the source DataFrame.

    Returns:
        A dict ready for the upsert statement, or ``None`` if the row is
        missing a required identifier (``national_id`` or ``name``) and
        must be skipped.
    """
    national_id = _normalize_national_id(row.get("شناسه ملی موسسه"))
    name = _clean_optional_text(row.get("نام موسسه"))
    if national_id is None or name is None:
        return None

    record: dict[str, Any] = {
        "national_id": national_id,
        "name": name,
        "tracking_code": _clean_optional_text(row.get("کد رهگیری")),
        "city": _clean_optional_text(row.get("شهر")),
        "address": _clean_optional_text(row.get("آدرس")),
        "province": _clean_optional_text(row.get("استان")) or DEFAULT_PROVINCE,
        "university_type": (
            _clean_optional_text(row.get("نوع موسسه")) or DEFAULT_UNIVERSITY_TYPE
        ),
        "status": _clean_optional_text(row.get("وضعیت")) or DEFAULT_STATUS,
        "is_deleted": False,
    }
    return record


def transform_dataframe(dataframe: pd.DataFrame) -> tuple[list[dict[str, Any]], int]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``national_id`` values within the source file are collapsed
    to the last occurrence, since PostgreSQL rejects an ``ON CONFLICT``
    batch that targets the same conflict key twice in one statement.

    Args:
        dataframe: The raw source worksheet.

    Returns:
        A tuple of (deduplicated records ready for upsert, skipped row
        count).
    """
    records_by_national_id: dict[str, dict[str, Any]] = {}
    skipped_count = 0

    for index, row in dataframe.iterrows():
        record = row_to_university_record(row)
        if record is None:
            skipped_count += 1
            logger.warning(
                "Row %d skipped: missing required national_id or name.",
                index + 2,  # +2: 1-indexed and header row offset.
            )
            continue
        records_by_national_id[record["national_id"]] = record

    return list(records_by_national_id.values()), skipped_count


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``national_id``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    insert_statement = pg_insert(University).values(records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[University.national_id],
        set_=update_columns,
    )


def run_upsert_import() -> None:
    """Execute the end-to-end upsert import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    records, skipped_count = transform_dataframe(dataframe)
    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        return

    statement = build_upsert_statement(records)

    session = SessionLocal()
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
    print("UNIVERSITY UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:         {len(dataframe)}")
    print(f"Rows skipped (invalid):   {skipped_count}")
    print(f"Rows processed (upsert):  {processed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()
