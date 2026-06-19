from sqlalchemy import Column, String, Text
from core.database import Base
from models.employer import SoftDeleteMixin


class University(SoftDeleteMixin, Base):
    """University/Executing Institution model"""
    __tablename__ = 'universities'
    
    national_id = Column(String(20), primary_key=True, comment='شناسه ملی موسسه')
    tracking_code = Column(String(50), nullable=True, comment='کد رهگیری')
    name = Column(String(200), nullable=False, comment='نام موسسه')
    city = Column(String(100), nullable=True, comment='شهر')
    address = Column(Text, nullable=True, comment='آدرس')
    province = Column(String(50), nullable=False, comment='استان موسسه')
    university_type = Column(String(100), nullable=False, comment='نوع موسسه')
    status = Column(String(20), nullable=False, default='Active', comment='وضعیت')
    
    def __repr__(self):
        return f"<University(national_id='{self.national_id}', name='{self.name}')>"
