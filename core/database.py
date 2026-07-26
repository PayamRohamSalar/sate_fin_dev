"""Database core for the SATE financial system.

Configures the SQLAlchemy engine, session factory, declarative ``Base`` class,
and the shared :class:`SoftDeleteMixin` used by every domain model to support
non-destructive (soft) deletion of records.

Soft-delete convention
----------------------
Every model inherits from both :data:`Base` and :class:`SoftDeleteMixin`.
Records are flagged via ``is_deleted`` rather than physically removed, which
preserves audit history and referential integrity across the dataset.
"""

import os

from sqlalchemy import Boolean, Column, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please configure it in .env.")

# Create engine with connection pooling settings
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class SoftDeleteMixin:
    """Mixin providing non-destructive (soft) deletion support.

    Columns
    -------
    is_deleted : bool
        Flag indicating whether the row is logically deleted. ``False`` means
        the record is live; ``True`` means it has been soft-deleted and should
        be excluded from active result sets. Indexed for query performance.
    """

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)


def get_db():
    """Yield a scoped database session and ensure it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
