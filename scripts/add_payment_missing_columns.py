"""Add missing payment tracking columns to an existing PostgreSQL database.

``models/payment.py`` declares ``payment_date``, ``execution_year``, and
``payment_type`` as ``nullable=False``, but the live ``payments`` table
predates those columns entirely (discovered while running
``scripts/import_payments_upsert.py`` against the local dev database).

This migration adds the three columns as **nullable**, not ``NOT NULL``:
1,277 of the table's 1,420 existing rows have no ``notification_date`` (the
column any real ``payment_date`` would be derived from for historical
data), so retroactively enforcing ``NOT NULL`` here would require either
fabricating placeholder dates for most of the table's history or blocking
the migration outright — neither is this script's call to make. Every row
written going forward by ``import_payments_upsert.py`` always supplies all
three columns, so the application-level guarantee holds for new data
without requiring a database-level constraint that legacy rows can't meet
yet. Promoting these columns to ``NOT NULL`` (matching the model exactly)
is a deliberate follow-up decision once a backfill strategy for the 1,277
historical rows is chosen.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from core.database import engine


def add_payment_missing_columns() -> None:
    """Add the nullable payment_date/execution_year/payment_type columns."""
    statement = text(
        """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS payment_date DATE NULL,
        ADD COLUMN IF NOT EXISTS execution_year INTEGER NULL,
        ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) NULL
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_payment_missing_columns()
    print("payment_date, execution_year, and payment_type columns are ready.")
