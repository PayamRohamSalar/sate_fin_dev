from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from models.employer import SoftDeleteMixin


class AnnualMandate(SoftDeleteMixin, Base):
    """Master table tracking mandated budget amounts per employer per fiscal year."""
    __tablename__ = 'annual_mandates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(22, 0), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('employer_code', 'fiscal_year', name='uq_employer_year_mandate'),
    )

    def __repr__(self):
        return f"<AnnualMandate(employer={self.employer_code}, year={self.fiscal_year}, amount={self.mandated_amount})>"


class DepositReceipt(SoftDeleteMixin, Base):
    """Detail table tracking individual deposit receipts per employer per fiscal year."""
    __tablename__ = 'deposit_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    deposit_amount = Column(Numeric(22, 0), nullable=False)
    deposit_date = Column(Date, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DepositReceipt(employer={self.employer_code}, year={self.fiscal_year}, amount={self.deposit_amount})>"
