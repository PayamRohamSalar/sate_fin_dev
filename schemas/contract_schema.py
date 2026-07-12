from typing import Optional

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
