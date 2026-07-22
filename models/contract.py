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
    proposal_id = Column(String(50), nullable=True)
    contract_number = Column(String(100), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    contract_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(22, 0), nullable=False)
    title = Column(Text, nullable=False)
    duration_months = Column(Integer, nullable=True)
    status = Column(String(50), default="Active")
