from typing import Optional

from pydantic import BaseModel, Field


class ResearcherCreate(BaseModel):
    """Payload for registering a new researcher (فناور)."""
    national_id: str = Field(..., min_length=10, max_length=10, description="National code of the researcher (10 digits)")
    full_name: str = Field(..., description="Full name of the researcher")
    university_national_id: str = Field(..., description="National ID of the affiliated university/institution")
    academic_rank: str = Field("سایر", description="Academic rank of the researcher")

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "1234567890",
                "full_name": "علی رضایی",
                "university_national_id": "14001234567",
                "academic_rank": "استادیار",
            }
        }


class ResearcherCreated(BaseModel):
    """Confirmation returned after a researcher is created."""
    national_id: str
    full_name: str
    university_id: str
    academic_rank: str
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "1234567890",
                "full_name": "علی رضایی",
                "university_id": "14001234567",
                "academic_rank": "استادیار",
                "status": "Active",
            }
        }
