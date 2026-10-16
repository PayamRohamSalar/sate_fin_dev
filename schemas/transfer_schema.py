"""Pydantic schemas for the credit-transfer (انتقال اعتبار) endpoints."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from services.financial_engine import TRANSFER_POOL_YEARS

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
        ...,
        description=(
            "Fiscal year the transferred funds originated from. Only the prior "
            "years' pool (1402 or 1404) is allowed -- current-year (1405) credit "
            "cannot be transferred."
        ),
    )
    amount: int = Field(..., gt=0, description="Transfer amount in whole Rials")
    broker_name: Optional[str] = Field(
        None, max_length=100, description="Optional broker facilitating the transfer"
    )
    documentation: Optional[str] = Field(
        None, description="Supporting documentation or free-text notes"
    )

    @field_validator("fiscal_year")
    @classmethod
    def _fiscal_year_in_transfer_pool(cls, value: int) -> int:
        if value not in TRANSFER_POOL_YEARS:
            years = " یا ".join(str(y) for y in TRANSFER_POOL_YEARS)
            raise ValueError(
                f"سال مالی انتقال اعتبار فقط می‌تواند {years} باشد "
                "(انتقال از محل اعتبار سال جاری امکان‌پذیر نیست)."
            )
        return value

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


class SourceBalanceResponse(BaseModel):
    """What a source employer can transfer, and what it cannot (all in Rials)."""

    employer_code: str
    pool_balance_1402_1404: int = Field(
        ..., description="Combined 1402+1404 balance after transfers -- the ceiling a transfer is checked against"
    )
    balance_1405: int = Field(
        ..., description="Current-year (1405) balance -- not transferable"
    )


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
    # Report-only enrichment, filled by the list endpoint (None on
    # create/update responses): the destination contract's total amount, the
    # sum of ALL active transfers funding that contract, and the source
    # employer's combined 1402+1404 balance before / after every one of
    # their transfers (see calculate_gross_pool_balance /
    # calculate_combined_pool_balance).
    contract_amount: Optional[int] = None
    contract_funded_total: Optional[int] = None
    source_balance_before_transfers: Optional[int] = None
    source_balance_after_transfers: Optional[int] = None

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
