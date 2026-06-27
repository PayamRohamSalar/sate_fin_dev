from pydantic import BaseModel, Field
from datetime import datetime
import jdatetime


class BalanceResponse(BaseModel):
    """
    Response schema for employer balance inquiry.

    Balance formula: (Total Deposits + Transfers In) - (Total Payments + Transfers Out)
    """
    employer_code: str = Field(..., description="The employer's classification code")
    funding_year: int = Field(..., description="The funding year (fiscal year) for the balance calculation")
    total_balance: float = Field(
        ...,
        description=(
            "The calculated real balance: "
            "(Total Deposits + Transfers In) - (Total Payments + Transfers Out)"
        ),
    )
    inquiry_date_jalali: str = Field(..., description="Current date in Persian/Jalali calendar format")

    class Config:
        json_schema_extra = {
            "example": {
                "employer_code": "EMP001",
                "funding_year": 1403,
                "total_balance": 125000000.50,
                "inquiry_date_jalali": "1403/03/30"
            }
        }

    @staticmethod
    def get_current_jalali_date() -> str:
        """
        Returns the current date in Jalali (Persian) calendar format.
        Format: YYYY/MM/DD
        """
        now = jdatetime.datetime.now()
        return now.strftime("%Y/%m/%d")
