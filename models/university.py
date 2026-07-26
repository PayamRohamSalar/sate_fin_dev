"""University (دانشگاه‌ها) model for the SATE financial system.

Represents a university or executing institution that supervises researchers
and administers research contracts on behalf of the funding program.
"""

from sqlalchemy import Column, String, Text

from core.database import Base, SoftDeleteMixin


class University(SoftDeleteMixin, Base):
    """University or executing institution.

    Attributes
    ----------
    national_id : str
        National identifier of the institution; primary key (max 20 chars).
    tracking_code : str or None
        Optional tracking code assigned to the institution.
    name : str
        Official name of the institution (max 200 chars).
    city : str or None
        City where the institution is located.
    address : str or None
        Postal address of the institution.
    province : str
        Province where the institution is located (max 50 chars).
    university_type : str
        Category/type of the institution (max 50 chars).
    status : str
        Lifecycle status; defaults to ``Active``.
    """

    __tablename__ = "universities"

    national_id = Column(String(20), primary_key=True, comment="شناسه ملی موسسه")
    tracking_code = Column(String(50), nullable=True, comment="کد رهگیری")
    name = Column(String(200), nullable=False, comment="نام موسسه")
    city = Column(String(100), nullable=True, comment="شهر")
    address = Column(Text, nullable=True, comment="آدرس")
    province = Column(String(50), nullable=False, comment="استان موسسه")
    university_type = Column(String(50), nullable=False, comment="نوع موسسه")
    status = Column(String(20), nullable=False, default="Active", comment="وضعیت")

    def __repr__(self):
        return f"<University(national_id={self.national_id!r}, name={self.name!r})>"
