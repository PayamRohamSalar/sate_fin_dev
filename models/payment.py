from sqlalchemy import Column, String, ForeignKey, Date, Numeric, Integer
from core.database import Base
from models.employer import SoftDeleteMixin


class Payment(SoftDeleteMixin, Base):
    __tablename__ = 'payments'

    tracking_code = Column(String(50), primary_key=True)
    contract_tracking_code = Column(String(50), ForeignKey('contracts.tracking_code'), nullable=False)
    series = Column(String(50), nullable=True)
    amount = Column(Numeric(22, 0), nullable=False)  # Base Rials
    notification_letter_number = Column(String(100), nullable=True)
    notification_date = Column(Date, nullable=True)
    payment_year = Column(Integer, nullable=False)  # Cash flow year
    funding_year = Column(Integer, nullable=False)  # Budget consumption year
    attachment_path = Column(String(255), nullable=True)
