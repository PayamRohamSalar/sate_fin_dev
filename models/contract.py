from sqlalchemy import Column, String, ForeignKey, Date, Numeric, Integer, Text
from core.database import Base
from models.employer import SoftDeleteMixin


class Contract(SoftDeleteMixin, Base):
    __tablename__ = 'contracts'

    tracking_code = Column(String(50), primary_key=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code'), nullable=False)
    university_id = Column(String(20), ForeignKey('universities.national_id'), nullable=False)
    researcher_id = Column(String(10), ForeignKey('researchers.national_code'), nullable=False)
    proposal_id = Column(String(50), nullable=True)  # Future FK
    contract_number = Column(String(100), nullable=True)
    contract_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(22, 0), nullable=False)  # Base Rials
    title = Column(Text, nullable=False)
    duration_months = Column(Integer, nullable=True)
    status = Column(String(50), default='Active')
