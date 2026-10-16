"""Add the reporting-only holding-company grouping column to ``employers``.

``models/employer.py`` now declares ``holding_company_code`` -- see that
column's docstring for the full explanation. In short: distinct from
``parent_code`` (which drives real financial roll-up for Subsidiary
employers everywhere in the system), this new column groups fully
financially-independent employers under an organizational holding company
purely for reporting (``services.financial_engine.get_holding_group_financials``).
No existing balance/roll-up function reads it.

Idempotent: safe to run more than once.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from core.database import engine


def add_holding_company_code_column() -> None:
    statement = text(
        """
        ALTER TABLE employers
        ADD COLUMN IF NOT EXISTS holding_company_code VARCHAR(20)
            REFERENCES employers(classification_code)
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_holding_company_code_column()
    print("employers.holding_company_code column is ready.")
