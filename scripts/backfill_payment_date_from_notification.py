"""Backfill payments.payment_date from payments.notification_date.

``payment_date`` (the real cash-disbursement date) has never actually been
populated in this database — every row relied on ``notification_date`` as a
proxy via ``COALESCE`` in ``services.financial_engine.get_contract_status_
overview`` (see that function's docstring). Per explicit instruction, this
script closes that gap directly at the data level: every ``payments`` row
with a ``NULL`` ``payment_date`` gets it set equal to its own
``notification_date``.

Only ``NULL`` ``payment_date`` rows are touched, and only when
``notification_date`` is itself non-``NULL`` — a row with both fields empty
has nothing to copy from and is left alone (and reported, not silently
skipped). Idempotent: safe to re-run at any time; it only ever affects rows
that still need it.

Usage
-----
    python scripts/backfill_payment_date_from_notification.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from core.database import SessionLocal  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("backfill_payment_date_from_notification")

UPDATE_STATEMENT = text(
    """
    UPDATE payments
    SET payment_date = notification_date
    WHERE payment_date IS NULL
      AND notification_date IS NOT NULL
    """
)

COUNT_REMAINING_NULL = text("SELECT COUNT(*) FROM payments WHERE payment_date IS NULL")
COUNT_TOTAL = text("SELECT COUNT(*) FROM payments")
COUNT_BOTH_NULL = text(
    """
    SELECT COUNT(*) FROM payments
    WHERE payment_date IS NULL AND notification_date IS NULL
    """
)


def run_backfill() -> None:
    """Set payment_date = notification_date for every row missing payment_date."""
    session = SessionLocal()
    try:
        result = session.execute(UPDATE_STATEMENT)
        updated_count = result.rowcount
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Backfill failed, transaction rolled back: %s", exc)
        session.close()
        return

    total = session.execute(COUNT_TOTAL).scalar()
    remaining_null = session.execute(COUNT_REMAINING_NULL).scalar()
    both_null = session.execute(COUNT_BOTH_NULL).scalar()
    session.close()

    print("\n" + "=" * 60)
    print("PAYMENT_DATE <- NOTIFICATION_DATE BACKFILL SUMMARY")
    print("=" * 60)
    print(f"Total rows in payments:                         {total}")
    print(f"Rows updated (payment_date <- notification_date): {updated_count}")
    print(f"Rows still NULL after backfill:                  {remaining_null}")
    print(f"  - of which notification_date is ALSO NULL:     {both_null}")
    print("=" * 60)


if __name__ == "__main__":
    run_backfill()
