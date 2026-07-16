from typing import Optional

from pydantic import BaseModel, Field


class UniversityCreate(BaseModel):
    """Payload for registering a new university / executing institution."""
    national_id: str = Field(..., min_length=1, max_length=20, description="National ID of the institution")
    name: str = Field(..., description="Full name of the institution")
    province: str = Field(..., description="Province where the institution is located")
    university_type: str = Field(..., description="Type of the institution")
    is_active: bool = Field(True, description="Active status (True = Active, False = Inactive)")

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "14001234567",
                "name": "دانشگاه نمونه",
                "province": "تهران",
                "university_type": "دانشگاه دولتی",
                "is_active": True,
            }
        }


class UniversityCreated(BaseModel):
    """Confirmation returned after a university is created."""
    national_id: str
    name: str
    province: str
    university_type: str
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "14001234567",
                "name": "دانشگاه نمونه",
                "province": "تهران",
                "university_type": "دانشگاه دولتی",
                "status": "Active",
            }
        }
