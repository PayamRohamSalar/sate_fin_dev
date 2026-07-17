from typing import Optional

from pydantic import BaseModel, Field


class ResearcherCreate(BaseModel):
    """Payload for registering a new researcher (فناور), aligned to models/researchers.py."""
    national_code: str = Field(..., min_length=10, max_length=10, description="National code of the researcher (10 digits)")
    first_name: str = Field(..., description="First name of the researcher")
    last_name: str = Field(..., description="Last name of the researcher")
    mobile: Optional[str] = Field(None, description="Mobile phone number")
    email: Optional[str] = Field(None, description="Email address")
    academic_rank: Optional[str] = Field(None, description="Academic rank")
    education_level: Optional[str] = Field(None, description="Education level")
    researcher_type: Optional[str] = Field(None, description="Researcher type")
    university_id: str = Field(..., description="National ID of the affiliated university/institution")
    status: str = Field("Active", description="Status: 'Active' or 'Inactive'")

    class Config:
        json_schema_extra = {
            "example": {
                "national_code": "1234567890",
                "first_name": "علی",
                "last_name": "رضایی",
                "mobile": "09123456789",
                "email": "ali@example.com",
                "academic_rank": "استادیار",
                "education_level": "دکتری",
                "researcher_type": "هیات علمی",
                "university_id": "14001234567",
                "status": "Active",
            }
        }


class ResearcherCreated(BaseModel):
    """Confirmation returned after a researcher is created."""
    national_code: str
    full_name: str
    university_id: str
    academic_rank: Optional[str] = None
    education_level: Optional[str] = None
    researcher_type: Optional[str] = None
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "national_code": "1234567890",
                "full_name": "علی رضایی",
                "university_id": "14001234567",
                "academic_rank": "استادیار",
                "education_level": "دکتری",
                "researcher_type": "هیات علمی",
                "status": "Active",
            }
        }
