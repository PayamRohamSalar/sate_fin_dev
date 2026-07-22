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


class PaymentBatchValidationRequest(BaseModel):
    """
    Request schema for validating a single drafted (cart) payment.

    The `pending_cart_amount` represents the sum of other drafted payments that
    target the SAME employer inside the frontend's temporary cart. It is
    subtracted from the current database balance so that the available balance
    reflects funds already reserved by not-yet-submitted drafts.
    """
    contract_tracking_code: str = Field(..., description="The contract tracking code linked to the payment")
    amount: float = Field(..., description="The payment amount to be validated", gt=0)
    funding_year: int = Field(..., description="The funding year for the payment", ge=1300, le=1500)
    pending_cart_amount: float = Field(
        0.0,
        ge=0,
        description="Sum of other drafted payments for the same employer in the cart",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "funding_year": 1403,
                "pending_cart_amount": 20000000.0,
            }
        }


class PaymentBatchValidationResponse(BaseModel):
    """
    Response schema returned when a drafted payment passes validation.
    """
    employer_code: str = Field(..., description="The employer classification code")
    current_db_balance: float = Field(..., description="Current balance from the database")
    pending_cart_amount: float = Field(..., description="Reserved amount from other drafts in the cart")
    available_balance: float = Field(..., description="Balance available after reserving cart drafts")
    amount: float = Field(..., description="The payment amount being validated")
    remaining_balance: float = Field(..., description="Available balance after this payment")
    is_valid: bool = Field(True, description="Whether the drafted payment is valid")


class PaymentBulkItem(BaseModel):
    """
    Single payment entry inside a bulk submission.
    """
    tracking_code: str = Field(..., description="Unique payment tracking code")
    contract_tracking_code: str = Field(..., description="Contract tracking code linked to the payment")
    amount: float = Field(..., description="Payment amount in base Rials", gt=0)
    payment_year: int = Field(..., description="Cash flow year", ge=1300, le=1500)
    funding_year: int = Field(..., description="Budget consumption year", ge=1300, le=1500)
    series: Optional[str] = Field(default=None, description="Payment series identifier")
    notification_letter_number: Optional[str] = Field(
        default=None,
        description="Notification letter number (optional; may be filled later via update form)",
    )
    notification_date: Optional[date] = Field(
        default=None,
        description="Notification date (optional; may be filled later via update form)",
    )
    attachment_path: Optional[str] = Field(default=None, description="Path to the payment attachment")

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "payment_year": 1403,
                "funding_year": 1403,
                "series": "Q1",
                "notification_letter_number": None,
                "notification_date": None,
                "attachment_path": None,
            }
        }


class PaymentBulkCreate(BaseModel):
    """
    Request schema for submitting a batch (cart) of payments at once.
    """
    payments: List[PaymentBulkItem] = Field(
        ..., min_length=1, description="List of payments to register in a single transaction"
    )


class PaymentBulkCreateResponse(BaseModel):
    """
    Response schema returned after a successful bulk submission.
    """
    message: str = Field(..., description="Human readable success message")
    submitted_count: int = Field(..., description="Number of payments committed")
    tracking_codes: List[str] = Field(..., description="Tracking codes of the committed payments")
    warning_messages: List[str] = Field(
        default_factory=list,
        description="Non-blocking FR-20 warnings for negative employer balances",
    )
