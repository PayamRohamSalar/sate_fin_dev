"""Add the payment lifecycle status column to an existing PostgreSQL database.

``models/payment.py`` now declares ``status`` (``"Draft"`` while staged in
the batch-payment cart, ``"Final"`` once confirmed — see
``api/v1/endpoints/payments.py``'s draft/finalize-batch endpoints). This
migration adds the column idempotently, defaulting existing and
future-unset rows to ``"Final"`` so every payment written before this
column existed is treated as already confirmed, matching its prior
behavior exactly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from core.database import engine


def add_payment_status_column() -> None:
    """Add the nullable, default-'Final' status column idempotently."""
    statement = text(
        """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Final'
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_payment_status_column()
    print("payments.status column is ready.")
