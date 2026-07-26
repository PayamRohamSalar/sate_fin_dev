"""Researcher (فناور) model for the SATE financial system.

Represents an individual researcher/technologist who is affiliated with a
university and may participate in one or more research contracts.
"""

from sqlalchemy import Column, ForeignKey, String

from core.database import Base, SoftDeleteMixin


class Researcher(SoftDeleteMixin, Base):
    """A researcher (فناور) affiliated with a university.

    Attributes
    ----------
    national_code : str
        Iranian national code; primary key (max 10 chars).
    tracking_code : str or None
        Optional tracking code assigned to the researcher.
    first_name : str
        Researcher's first name (max 100 chars).
    last_name : str
        Researcher's last name (max 100 chars).
    full_name : str
        Full display name of the researcher (max 200 chars).
    mobile : str or None
        Contact mobile number.
    email : str or None
        Contact email address.
    academic_rank : str or None
        Academic rank/position (max 50 chars).
    university_id : str
        Foreign key to ``universities.national_id``.
    education_level : str or None
        Highest education level attained.
    researcher_type : str or None
        Category/type of researcher.
    status : str
        Lifecycle status; defaults to ``Active``.
    """

    __tablename__ = "researchers"

    national_code = Column(String(10), primary_key=True)
    tracking_code = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    mobile = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    academic_rank = Column(String(50), nullable=True)
    university_id = Column(
        String(20),
        ForeignKey("universities.national_id"),
        nullable=False,
    )
    education_level = Column(String(50), nullable=True)
    researcher_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="Active")

    def __repr__(self):
        return f"<Researcher(national_code={self.national_code!r}, full_name={self.full_name!r})>"
