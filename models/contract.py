from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text

from core.database import Base
from models.employer import SoftDeleteMixin


class Contract(SoftDeleteMixin, Base):
    """Represent a research contract registered in the financial system."""

    __tablename__ = "contracts"

    tracking_code = Column(String(50), primary_key=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=False,
    )
    university_id = Column(
        String(20),
        ForeignKey("universities.national_id"),
        nullable=False,
    )
    researcher_id = Column(
        String(10),
        ForeignKey("researchers.national_code"),
        nullable=False,
    )
    # Link to the winning Proposal (models.proposal.Proposal.id), NOT a
    # declared ForeignKey -- the proposals table postdates this column, so
    # the link was validated empirically (2026-09) rather than enforced by
    # the schema. Three shapes exist in the data:
    #   - a real Proposal.id (~1168 contracts): the genuine link. Use
    #     Proposal.contract (see models/proposal.py) rather than querying
    #     this column directly.
    #   - equal to this row's own tracking_code (~773 contracts): a
    #     pre-existing placeholder from before the proposals table existed,
    #     NOT a real link. Always exclude proposal_id == tracking_code
    #     before treating this column as a proposal reference.
    #   - some other non-numeric legacy value (~49 contracts): unresolved.
    proposal_id = Column(String(50), nullable=True)
    contract_number = Column(String(100), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    contract_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(22, 0), nullable=False)
    title = Column(Text, nullable=False)
    duration_months = Column(Integer, nullable=True)
    status = Column(String(50), default="Active")
