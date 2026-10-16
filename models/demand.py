"""Demand (تقاضا) model for the SATE financial system.

A demand is a research/technology need an employer posts in the SATE
system, calling for proposals from universities and researchers. Sourced
from a full export of the system's demand registry (``All_Demands.xlsx``).
"""

from sqlalchemy import Column, Date, String, Text

from core.database import Base, SoftDeleteMixin


class Demand(SoftDeleteMixin, Base):
    """A research/technology demand (فراخوان) posted by an employer.

    Attributes
    ----------
    tracking_code : str
        Unique tracking code assigned by the SATE system; primary key.
    applicant_name : str
        Employer name exactly as it appears in the source export
        ("متقاضی"). Free text -- see ``employer_code``.
    employer_code : str or None
        Classification code of the matching ``Employer``, resolved by
        exact name match against ``applicant_name``. Informational only
        (not a enforced foreign key): a real employer may be missing here
        simply because its registered name differs slightly (spacing,
        legal-form prefix, etc.) from the source export's free-text value.
    demand_group : str
        Broad category of the demand ("گروه تقاضا", e.g. "پژوهش کاربردی").
    funding_source : str
        Budget line the demand is funded from ("محل تامین اعتبار").
    demand_nature : str or None
        High-level scientific nature of the demand ("ماهیت تقاضا").
    demand_domain : str or None
        Detailed subject-matter domain of the demand ("حوزه تقاضا").
    title : str
        Title of the demand ("عنوان تقاضا").
    demand_type : str or None
        Type/format of the requested work ("نوع تقاضا", e.g. "فناوری").
    demand_date : date or None
        Date the demand was posted, converted from the source's Jalali
        date ("تاریخ تقاضا").
    """

    __tablename__ = "demands"

    tracking_code = Column(String(20), primary_key=True)
    applicant_name = Column(String(300), nullable=False)
    employer_code = Column(String(20), nullable=True, index=True)
    demand_group = Column(String(100), nullable=True)
    funding_source = Column(String(200), nullable=True)
    demand_nature = Column(String(200), nullable=True)
    demand_domain = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    demand_type = Column(String(100), nullable=True)
    demand_date = Column(Date, nullable=True)

    def __repr__(self):
        return f"<Demand(tracking_code={self.tracking_code!r}, applicant={self.applicant_name!r})>"
