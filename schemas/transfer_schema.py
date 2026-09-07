"""Pydantic schemas for the credit-transfer (انتقال اعتبار) endpoints."""

from typing import Optional

from pydantic import BaseModel, Field

DEFAULT_DESTINATION_EMPLOYER_CODE = "128342"


class CreditTransferCreate(BaseModel):
    """Payload accepted when registering a new credit transfer."""

    source_employer_code: str = Field(
        ..., max_length=20, description="Employer the funds originate from"
    )
    destination_employer_code: str = Field(
        DEFAULT_DESTINATION_EMPLOYER_CODE,
        max_length=20,
        description="Employer the funds are transferred to (defaults to the Secretariat)",
    )
    contract_tracking_code: str = Field(
        ..., max_length=50, description="Contract receiving the transferred funds"
    )
    fiscal_year: int = Field(
        ..., ge=1300, le=1500, description="Fiscal year the transferred funds originated from"
    )
    amount: int = Field(..., gt=0, description="Transfer amount in whole Rials")
    broker_name: Optional[str] = Field(
        None, max_length=100, description="Optional broker facilitating the transfer"
    )
    documentation: Optional[str] = Field(
        None, description="Supporting documentation or free-text notes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source_employer_code": "EMP001",
                "destination_employer_code": "128342",
                "contract_tracking_code": "CNT-1403-001",
                "fiscal_year": 1404,
                "amount": 50000000,
                "broker_name": None,
                "documentation": "انتقال مانده مازاد طی اصلاحیه تبصره ۲ ماده ۵",
            }
        }


class CreditTransferUpdate(CreditTransferCreate):
    """Payload accepted when updating an existing credit transfer.

    Identical shape to :class:`CreditTransferCreate` -- the surrogate ``id``
    primary key is supplied via the URL path and is never changed by an
    update.
    """


class CreditTransferResponse(BaseModel):
    """One credit transfer enriched with display names, for report/edit UIs."""

    id: int = Field(..., description="Auto-incrementing credit transfer ID")
    source_employer_code: str
    source_employer_name: Optional[str] = None
    destination_employer_code: str
    destination_employer_name: Optional[str] = None
    contract_tracking_code: str
    contract_title: Optional[str] = None
    fiscal_year: int
    amount: int
    broker_name: Optional[str] = None
    documentation: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12,
                "source_employer_code": "EMP001",
                "source_employer_name": "وزارت نمونه",
                "destination_employer_code": "128342",
                "destination_employer_name": "دبیرخانه",
                "contract_tracking_code": "CNT-1403-001",
                "contract_title": "پروژه پژوهشی نمونه",
                "fiscal_year": 1404,
                "amount": 50000000,
                "broker_name": None,
                "documentation": "انتقال مانده مازاد طی اصلاحیه تبصره ۲ ماده ۵",
            }
        }
