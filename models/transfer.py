"""Credit Transfer model for the SATE financial system.

Junction table allocating unspent funds from one employer to a specific
contract, typically routed through the central Secretariat, without altering
the core deposit/payment tables.
"""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from core.database import Base, SoftDeleteMixin


class CreditTransfer(SoftDeleteMixin, Base):
    """Track fund transfers between employers.

    Allows allocation of unspent funds from various employers to contracts
    managed by a central Secretariat without altering the core deposit/payment
    tables.

    Attributes
    ----------
    id : int
        Auto-incrementing surrogate primary key.
    source_employer_code : str
        Employer the funds originate from (FK to ``employers.classification_code``).
    destination_employer_code : str
        Employer the funds are transferred to (FK to ``employers``); defaults to
        the Secretariat.
    broker_name : str or None
        Optional broker facilitating the transfer.
    fiscal_year : int
        Fiscal year the transferred funds originated from.
    amount : Decimal
        Transfer amount in Rials.
    contract_tracking_code : str
        Contract receiving the transferred funds (FK to ``contracts.tracking_code``).
    documentation : str or None
        Supporting documentation or free-text notes.
    """

    __tablename__ = "credit_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=False,
        index=True,
    )

    destination_employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=False,
        default="128342",
        index=True,
    )

    broker_name = Column(String(100), nullable=True)

    fiscal_year = Column(Integer, nullable=False, index=True)

    amount = Column(Numeric(22, 0), nullable=False)

    contract_tracking_code = Column(
        String(50),
        ForeignKey("contracts.tracking_code"),
        nullable=False,
        index=True,
    )

    contract = relationship("Contract", backref="credit_transfers")

    documentation = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<CreditTransfer(id={self.id}, from={self.source_employer_code}, "
            f"to={self.destination_employer_code}, amount={self.amount}, "
            f"year={self.fiscal_year})>"
        )
