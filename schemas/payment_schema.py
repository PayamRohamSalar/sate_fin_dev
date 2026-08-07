from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PaymentValidationRequest(BaseModel):
    """
    Request schema for validating a payment before registration.
    """
    contract_tracking_code: str = Field(..., description="The contract tracking code linked to the payment")
    amount: float = Field(..., description="The payment amount to be validated", gt=0)
    funding_year: int = Field(..., description="The funding year for the payment", ge=1300, le=1500)

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "funding_year": 1403
            }
        }


class PaymentValidationResponse(BaseModel):
    """
    Response schema for payment validation results.
    """
    employer_code: str = Field(..., description="The employer classification code")
    current_balance: float = Field(..., description="Current balance before the payment")
    payment_amount: float = Field(..., description="The payment amount being validated")
    new_balance: float = Field(..., description="Projected balance after the payment")
    is_negative: bool = Field(..., description="Whether the new balance will be negative")
    warning_message: Optional[str] = Field(None, description="Warning message if balance becomes negative")

    class Config:
        json_schema_extra = {
            "example": {
                "employer_code": "EMP001",
                "current_balance": 125000000.0,
                "payment_amount": 50000000.0,
                "new_balance": 75000000.0,
                "is_negative": False,
                "warning_message": None
            }
        }


class PaymentDraftCreate(BaseModel):
    """
    Request schema for staging one payment as a database-backed draft.

    A draft immediately reserves its ``amount`` against the linked
    employer's real balance (``calculate_real_balance`` sums ``Draft`` and
    ``Final`` payments alike) — insufficient funds reject the request with
    HTTP 400 rather than allowing an over-committed draft to be staged.
    """
    tracking_code: str = Field(..., description="Unique payment tracking code")
    contract_tracking_code: str = Field(..., description="Contract tracking code linked to the payment")
    amount: float = Field(..., description="Payment amount in base Rials", gt=0)
    funding_year: int = Field(..., description="Budget consumption (balance-reserving) year", ge=1300, le=1500)
    payment_year: Optional[int] = Field(default=None, description="Cash flow year", ge=1300, le=1500)
    series: Optional[str] = Field(default=None, description="Payment series/batch identifier")
    notification_letter_number: Optional[str] = Field(
        default=None, description="Notification letter number"
    )
    notification_date: Optional[date] = Field(default=None, description="Notification date")

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "funding_year": 1403,
                "payment_year": 1403,
                "series": "15",
                "notification_letter_number": None,
                "notification_date": None,
            }
        }


class PaymentDraftResponse(BaseModel):
    """
    Response schema representing one payment draft (or a finalized payment).

    Carries the linked contract's title/amount, employer name, and
    university name alongside the raw codes, so the frontend drafts table
    can display and export a fully readable row without a second lookup
    round-trip per row.
    """
    tracking_code: str = Field(..., description="Unique payment tracking code")
    contract_tracking_code: str = Field(..., description="Contract tracking code linked to the payment")
    contract_title: Optional[str] = Field(None, description="Title of the linked contract")
    contract_total_amount: Optional[float] = Field(
        None, description="Total amount of the linked contract, in base Rials"
    )
    employer_code: Optional[str] = Field(None, description="Classification code of the linked employer")
    employer_name: Optional[str] = Field(None, description="Name of the linked employer")
    university_name: Optional[str] = Field(
        None, description="Name of the university/institution executing the contract"
    )
    amount: float = Field(..., description="Payment amount in base Rials")
    funding_year: int = Field(..., description="Budget consumption (balance-reserving) year")
    payment_year: Optional[int] = Field(None, description="Cash flow year")
    series: Optional[str] = Field(None, description="Payment series/batch identifier")
    status: str = Field(..., description="'Draft' or 'Final'")
    employer_balance_after: Optional[float] = Field(
        None,
        description=(
            "Employer's real balance immediately after this payment, "
            "computed in sequence with any other listed drafts for the "
            "same employer/funding_year"
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "contract_title": "پروژه پژوهشی نمونه",
                "contract_total_amount": 1000000000.0,
                "employer_code": "EMP001",
                "employer_name": "وزارت نمونه",
                "university_name": "دانشگاه نمونه",
                "amount": 50000000.0,
                "funding_year": 1403,
                "payment_year": 1403,
                "series": "15",
                "status": "Draft",
                "employer_balance_after": 75000000.0,
            }
        }


class PaymentDraftCreateResponse(PaymentDraftResponse):
    """
    Response schema returned after successfully creating one draft.

    Extends :class:`PaymentDraftResponse` with the employer's balance
    immediately *before* this payment, so the frontend can show a full
    before/after transition without a separate API call.
    """
    employer_balance_before: float = Field(
        ..., description="Employer's real balance immediately before this payment"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "contract_title": "پروژه پژوهشی نمونه",
                "contract_total_amount": 1000000000.0,
                "employer_code": "EMP001",
                "employer_name": "وزارت نمونه",
                "university_name": "دانشگاه نمونه",
                "amount": 50000000.0,
                "funding_year": 1403,
                "payment_year": 1403,
                "series": "15",
                "status": "Draft",
                "employer_balance_before": 125000000.0,
                "employer_balance_after": 75000000.0,
            }
        }


class DraftDeleteResponse(BaseModel):
    """Response schema confirming a draft was removed."""
    message: str = Field(..., description="Human readable confirmation message")
    tracking_code: str = Field(..., description="Tracking code of the removed draft")


class FinalizeBatchRequest(BaseModel):
    """Request schema for finalizing every draft in a given series."""
    series: str = Field(..., min_length=1, description="Payment series/batch identifier to finalize")

    class Config:
        json_schema_extra = {"example": {"series": "15"}}


class FinalizeBatchResponse(BaseModel):
    """Response schema returned after finalizing a batch."""
    message: str = Field(..., description="Human readable success message")
    series: str = Field(..., description="Payment series/batch identifier that was finalized")
    finalized_count: int = Field(..., description="Number of drafts moved to 'Final' status")
    finalized_payments: List[PaymentDraftResponse] = Field(
        default_factory=list,
        description="The full enriched records that were finalized, for client-side reporting/export",
    )
