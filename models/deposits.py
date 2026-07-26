"""Deposit (نظارت بر واریز) models for the SATE financial system.

This module defines the domain models used to monitor mandated budgets and the
deposits actually received from each employer.

Tables
------
Deposit
    Spec-defined aggregate record tying the mandated amount and the deposited
    amount for a given employer and fiscal year. Enforces a composite unique
    constraint on ``(employer_code, fiscal_year)`` so that there is exactly one
    mandate/deposit summary per employer-year pair.
AnnualMandate
    Master record of the mandated budget amount per employer per fiscal year.
DepositReceipt
    Detail record of an individual deposit receipt per employer per fiscal year.
"""

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from core.database import Base, SoftDeleteMixin


class Deposit(SoftDeleteMixin, Base):
    """Aggregate mandate-vs-deposit summary for one employer in one fiscal year.

    Attributes
    ----------
    id : int
        Auto-incrementing surrogate primary key.
    employer_code : str
        Foreign key to ``employers.classification_code``.
    fiscal_year : int
        Fiscal (Persian-calendar) year the record applies to.
    mandated_amount : Decimal
        Amount mandated for the employer in the given year.
    deposit_amount : Decimal
        Amount actually deposited by the employer in the given year.
    deposit_date : date or None
        Date the deposit was made, when known.
    receipt_number : str or None
        Reference number of the deposit receipt, when available.

    Notes
    -----
    A composite unique constraint on ``(employer_code, fiscal_year)`` guarantees
    a single summary row per employer-year combination.
    """

    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(18, 2), nullable=False)
    deposit_amount = Column(Numeric(18, 2), nullable=False)
    deposit_date = Column(Date, nullable=True)
    receipt_number = Column(String(50), nullable=True)

    employer = relationship("Employer", backref="deposits")

    __table_args__ = (
        UniqueConstraint("employer_code", "fiscal_year", name="uq_deposit_employer_year"),
    )

    def __repr__(self):
        return (
            f"<Deposit(employer={self.employer_code}, year={self.fiscal_year}, "
            f"mandated={self.mandated_amount}, deposited={self.deposit_amount})>"
        )


class AnnualMandate(SoftDeleteMixin, Base):
    """Master record tracking mandated budget amounts per employer per fiscal year."""

    __tablename__ = "annual_mandates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(22, 0), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("employer_code", "fiscal_year", name="uq_employer_year_mandate"),
    )

    def __repr__(self):
        return f"<AnnualMandate(employer={self.employer_code}, year={self.fiscal_year}, amount={self.mandated_amount})>"


class DepositReceipt(SoftDeleteMixin, Base):
    """Detail record tracking individual deposit receipts per employer per fiscal year."""

    __tablename__ = "deposit_receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year = Column(Integer, nullable=False, index=True)
    deposit_amount = Column(Numeric(22, 0), nullable=False)
    deposit_date = Column(Date, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DepositReceipt(employer={self.employer_code}, year={self.fiscal_year}, amount={self.deposit_amount})>"
