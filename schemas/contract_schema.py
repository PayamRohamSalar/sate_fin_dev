from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class ContractSearchResult(BaseModel):
    """
    Single contract match returned by the contract search (auto-fill) endpoint.
    """
    contract_tracking_code: str = Field(..., description="The contract tracking code")
    title: str = Field(..., description="The contract title")
    employer_name: Optional[str] = Field(None, description="Name of the linked employer")
    employer_classification_code: Optional[str] = Field(
        None, description="Classification code of the linked employer"
    )
    university_name: Optional[str] = Field(None, description="Name of the executing university")
    researcher_name: Optional[str] = Field(None, description="Full name of the researcher")

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "title": "\u067e\u0631\u0648\u0698\u0647 \u067e\u0698\u0648\u0647\u0634\u06cc \u0646\u0645\u0648\u0646\u0647",
                "employer_name": "\u0648\u0632\u0627\u0631\u062a \u0646\u0645\u0648\u0646\u0647",
                "employer_classification_code": "EMP001",
                "university_name": "\u062f\u0627\u0646\u0634\u06af\u0627\u0647 \u0646\u0645\u0648\u0646\u0647",
                "researcher_name": "\u0639\u0644\u06cc \u0631\u0636\u0627\u06cc\u06cc",
            }
        }


class ContractCreate(BaseModel):
    """
    Payload for registering a new contract via the data-entry form.
    """
    tracking_code: str = Field(..., description="The contract tracking code (primary key)")
    employer_classification_code: str = Field(..., description="Classification code of the contracting employer")
    university_national_id: str = Field(..., description="National ID of the executing university")
    researcher_national_id: str = Field(..., description="National code of the lead researcher")
    title: str = Field(..., description="Contract / project title")
    total_amount: float = Field(..., description="Total contract amount in Rials")
    contract_date: date = Field(..., description="Contract date (ISO date or YYYY-MM-DD)")
    duration_months: int = Field(..., description="Contract duration in months")

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "CNT-1403-002",
                "employer_classification_code": "EMP001",
                "university_national_id": "UNI001",
                "researcher_national_id": "1234567890",
                "title": "پروژه تحقیقاتی نمونه",
                "total_amount": 1000000000.0,
                "contract_date": "2024-03-20",
                "duration_months": 12,
            }
        }
