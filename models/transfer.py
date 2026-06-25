"""
Credit Transfer Model
Junction table for allocating unspent funds from employers to specific contracts
"""

from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey
from core.database import Base
from models.employer import SoftDeleteMixin


class CreditTransfer(Base, SoftDeleteMixin):
    """
    Credit Transfer model - tracks fund transfers between employers.
    Allows allocation of unspent funds from various employers to contracts
    managed by a central Secretariat without altering core deposit/payment tables.
    """
    __tablename__ = 'credit_transfers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source employer (where funds come from)
    source_employer_code = Column(
        String,
        ForeignKey('employers.classification_code'),
        nullable=False,
        index=True
    )
    
    # Destination employer (where funds go to, default is Secretariat)
    destination_employer_code = Column(
        String,
        ForeignKey('employers.classification_code'),
        nullable=False,
        default='128342',
        index=True
    )
    
    # Optional broker facilitating the transfer
    broker_name = Column(String, nullable=True)
    
    # Fiscal year the funds originated from
    fiscal_year = Column(Integer, nullable=False, index=True)
    
    # Transfer amount in Rials
    amount = Column(Numeric(22, 0), nullable=False)
    
    # Contract receiving the transferred funds
    contract_tracking_code = Column(
        String,
        ForeignKey('contracts.tracking_code'),
        nullable=False,
        index=True
    )
    
    # Supporting documentation or notes
    documentation = Column(Text, nullable=True)
    
    def __repr__(self):
        return (
            f"<CreditTransfer(id={self.id}, "
            f"from={self.source_employer_code}, "
            f"to={self.destination_employer_code}, "
            f"amount={self.amount}, "
            f"year={self.fiscal_year})>"
        )
