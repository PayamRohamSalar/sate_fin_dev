"""Add contract attachment storage to an existing PostgreSQL database."""

from sqlalchemy import text

from core.database import engine


def add_contract_attachment_path() -> None:
    """Add the nullable attachment path column idempotently."""
    statement = text(
        """
        ALTER TABLE contracts
        ADD COLUMN IF NOT EXISTS attachment_path VARCHAR(255) NULL
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_contract_attachment_path()
    print("Contract attachment_path column is ready.")
