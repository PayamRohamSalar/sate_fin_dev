"""Trustee Payments Table Initialization Script.

Safely creates the ``trustee_payments`` table without touching any existing
table. Mirrors ``scripts/create_transfer_table.py``'s pattern: a targeted
``Base.metadata.create_all(..., tables=[...])`` call, which is idempotent
(no-op if the table already exists) and never issues a ``DROP``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import Base, engine
from models.trustee_payments import TrusteePayment


def main() -> int:
    """Create the trustee_payments table if it does not already exist."""
    print("=" * 60)
    print("Trustee Payments ('پرداخت‌های امانی') Table Initialization")
    print("=" * 60)

    print("\nCreating trustee_payments table...")
    try:
        Base.metadata.create_all(bind=engine, tables=[TrusteePayment.__table__])
        print("Successfully created (or confirmed existing) trustee_payments table.")
        print("\nTable structure:")
        print("  - id (Integer, Primary Key)")
        print("  - tracking_code (String, unique, indexed)")
        print("  - contract_tracking_code (String, indexed, NOT a foreign key)")
        print("  - employer_code (String, indexed, informational only)")
        print("  - amount (Numeric(22,0))")
        print("  - payment_year (Integer, nullable)")
        print("  - notification_letter_number (String, nullable)")
        print("  - notification_date (Date, nullable)")
        print("  - source_note (Text, nullable)")
        print("  - is_deleted (from SoftDeleteMixin)")
        print("\n" + "=" * 60)
        print("Table initialization completed successfully.")
        print("=" * 60)
    except Exception as exc:
        print(f"Error creating table: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
