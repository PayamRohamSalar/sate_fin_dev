"""Demand/Proposal Tables Initialization Script.

Safely creates the ``demands`` and ``proposals`` tables without touching
any existing table. Mirrors ``scripts/create_trustee_payments_table.py``'s
pattern: a targeted ``Base.metadata.create_all(..., tables=[...])`` call,
which is idempotent (no-op if the tables already exist) and never issues a
``DROP``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import Base, engine
from models.demand import Demand
from models.proposal import Proposal


def main() -> int:
    """Create the demands/proposals tables if they do not already exist."""
    print("=" * 60)
    print("Demand ('تقاضا') / Proposal ('پیشنهاده') Tables Initialization")
    print("=" * 60)

    print("\nCreating demands and proposals tables...")
    try:
        Base.metadata.create_all(bind=engine, tables=[Demand.__table__, Proposal.__table__])
        print("Successfully created (or confirmed existing) demands/proposals tables.")
        print("\ndemands columns:")
        print("  - tracking_code (String, Primary Key)")
        print("  - applicant_name (String)")
        print("  - employer_code (String, indexed, informational only)")
        print("  - demand_group, funding_source, demand_nature, demand_domain, title, demand_type")
        print("  - demand_date (Date, nullable)")
        print("  - is_deleted (from SoftDeleteMixin)")
        print("\nproposals columns:")
        print("  - id (Integer, Primary Key -- taken verbatim from the source export)")
        print("  - demand_tracking_code (String, indexed, informational only)")
        print("  - researcher_name, researcher_code (indexed, informational only)")
        print("  - university_name, university_id (indexed, informational only)")
        print("  - status_code, status_title")
        print("  - submitted_at (DateTime, nullable)")
        print("  - is_deleted (from SoftDeleteMixin)")
        print("\n" + "=" * 60)
        print("Table initialization completed successfully.")
        print("=" * 60)
    except Exception as exc:
        print(f"Error creating tables: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
