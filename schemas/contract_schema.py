from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ContractSearchResult(BaseModel):
    """Represent one active contract returned to API consumers."""

    contract_tracking_code: str = Field(
        ..., description="The contract tracking code"
    )
    title: str = Field(..., description="The contract title")
    employer_name: Optional[str] = Field(
        None, description="Name of the linked employer"
    )
    employer_classification_code: Optional[str] = Field(
        None, description="Classification code of the linked employer"
    )
    university_name: Optional[str] = Field(
        None, description="Name of the executing university"
    )
    researcher_name: Optional[str] = Field(
        None, description="Full name of the researcher"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "title": "پروژه پژوهشی نمونه",
                "employer_name": "وزارت نمونه",
                "employer_classification_code": "EMP001",
                "university_name": "دانشگاه نمونه",
                "researcher_name": "علی رضایی",
            }
        }


class ContractCreate(BaseModel):
    """Define the payload accepted when registering a new contract."""

    tracking_code: str = Field(
        ..., min_length=1, description="The contract tracking code (primary key)"
    )
    employer_classification_code: str = Field(
        ..., description="Classification code of the contracting employer"
    )
    university_national_id: str = Field(
        ..., description="National ID of the executing university"
    )
    researcher_national_id: str = Field(
        ..., description="National code of the lead researcher"
    )
    contract_number: Optional[str] = Field(
        None, description="Operational contract number"
    )
    proposal_id: Optional[str] = Field(
        None, description="Identifier of the linked proposal"
    )
    attachment_path: Optional[str] = Field(
        None, description="Local path of the archived contract document"
    )
    title: str = Field(
        ..., min_length=1, description="Contract or project title"
    )
    total_amount: float = Field(
        ..., gt=0, description="Total contract amount in Rials"
    )
    contract_date: date = Field(
        ..., description="Contract date in Gregorian ISO format"
    )
    duration_months: int = Field(
        ..., gt=0, description="Contract duration in months"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "CNT-1403-002",
                "employer_classification_code": "EMP001",
                "university_national_id": "UNI001",
                "researcher_national_id": "1234567890",
                "contract_number": "1403/CON/002",
                "proposal_id": "PRP-1403-002",
                "attachment_path": "data/Archive/Contracts/example.pdf",
                "title": "پروژه تحقیقاتی نمونه",
                "total_amount": 1000000000.0,
                "contract_date": "2024-03-20",
                "duration_months": 12,
            }
        }
