from sqlalchemy import Column, String, Boolean, CheckConstraint
from core.database import Base

class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

class Employer(SoftDeleteMixin, Base):
    __tablename__ = 'employers'

    classification_code = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    employer_type = Column(String(20), nullable=False)
    parent_code = Column(String(20), nullable=True)
    province = Column(String(50), nullable=False)
    affairs_category = Column(String(100), nullable=True)
    upper_organization = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default='Active')

    __table_args__ = (
        CheckConstraint("employer_type IN ('Mother', 'Subsidiary', 'Independent')", name="check_employer_type"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="check_employer_status"),
    )