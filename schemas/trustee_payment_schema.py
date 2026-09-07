"""Pydantic schemas for the trustee (custodial) payment registration endpoint.

A trustee payment ("پرداخت امانی") is recorded purely for contract-status
reconciliation -- see ``models.trustee_payments`` for why neither
``contract_tracking_code`` nor ``employer_code`` is a foreign key here.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class TrusteePaymentCreate(BaseModel):
    """Request schema for registering one trustee payment record."""

    tracking_code: str = Field(
        ..., min_length=1, description="Unique tracking code from the source reconciliation file"
    )
    contract_tracking_code: Optional[str] = Field(
        None, description="Related contract tracking code (informational only, not enforced as FK)"
    )
    employer_code: Optional[str] = Field(
        None, description="Related employer classification code (informational only, not enforced as FK)"
    )
    amount: int = Field(..., gt=0, description="Payment amount in whole Rials")
    payment_year: Optional[int] = Field(
        None, ge=1300, le=1500, description="Fiscal (Persian-calendar) year the payment was recorded against"
    )
    notification_letter_number: Optional[str] = Field(
        None, description="Notification letter reference number"
    )
    notification_date: Optional[date] = Field(None, description="Notification letter date")
    source_note: Optional[str] = Field(
        None, description="Free-text note documenting where this record came from"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "TP-1405-001",
                "contract_tracking_code": "CNT-1403-001",
                "employer_code": "EMP001",
                "amount": 50000000,
                "payment_year": 1405,
                "notification_letter_number": "12345",
                "notification_date": "1405-03-01",
                "source_note": "صورت تطبیق دانشگاه الف - مرداد ۱۴۰۵",
            }
        }


class TrusteePaymentCreateResponse(BaseModel):
    """Response returned after successfully registering a trustee payment."""

    id: int = Field(..., description="Auto-incrementing trustee payment ID")
    tracking_code: str
    contract_tracking_code: Optional[str] = None
    employer_code: Optional[str] = None
    employer_name: Optional[str] = Field(
        None, description="Resolved employer display name, when employer_code matches an active employer"
    )
    amount: int
    payment_year: Optional[int] = None
    notification_letter_number: Optional[str] = None
    notification_date: Optional[date] = None
    source_note: Optional[str] = None
    message: str = Field(..., description="Localized confirmation message")
