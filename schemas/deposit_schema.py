"""Pydantic schemas for the employer deposit registration endpoints."""

from typing import List, Optional

from pydantic import BaseModel, Field


class YearBalance(BaseModel):
    """Real financial balance for one employer in one fiscal year."""

    fiscal_year: int = Field(..., description="Fiscal (Persian-calendar) year")
    balance: float = Field(..., description="Real balance in base Rials")


class EmployerBalancesResponse(BaseModel):
    """Real balances for an employer across the configured target fiscal years."""

    employer_code: str = Field(..., description="Employer classification code")
    balances: List[YearBalance] = Field(
        ..., description="Balance breakdown per target fiscal year"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "employer_code": "EMP001",
                "balances": [
                    {"fiscal_year": 1402, "balance": 50000000},
                    {"fiscal_year": 1404, "balance": -12000000},
                    {"fiscal_year": 1405, "balance": 0},
                ],
            }
        }


class DepositReceiptCreateResponse(BaseModel):
    """Response returned after successfully registering a deposit receipt."""

    id: int = Field(..., description="Auto-incrementing deposit receipt ID")
    employer_code: str = Field(..., description="Employer classification code")
    employer_name: str = Field(..., description="Employer display name")
    fiscal_year: int = Field(..., description="Target fiscal year of the deposit")
    deposit_amount: int = Field(..., description="Deposited amount in whole Rials")
    attachment_path: Optional[str] = Field(
        None, description="Project-relative path of the archived receipt file"
    )
    description: Optional[str] = Field(
        None, description="Optional deposit description/title (شرح/عنوان واریز)"
    )
    message: str = Field(..., description="Localized confirmation message")
