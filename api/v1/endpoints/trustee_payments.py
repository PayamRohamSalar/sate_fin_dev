"""Trustee (custodial) payment registration endpoints for the SATE financial system.

A trustee payment is a disbursement paid directly by the executing
university/institution out of its own funds, entirely outside the
employer-managed budget pool -- see ``models.trustee_payments`` for the full
rationale. It is recorded here purely for reconciliation and must never feed
into any balance calculation.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import DataError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from core.database import get_db
from models.employer import Employer
from models.trustee_payments import TrusteePayment
from schemas.trustee_payment_schema import TrusteePaymentCreate, TrusteePaymentCreateResponse

router = APIRouter(prefix="/trustee-payments", tags=["Trustee Payments"])
logger = logging.getLogger(__name__)

CONNECTION_ERROR_MESSAGE = (
    "خطا در ارتباط با پایگاه داده. لطفاً چند لحظه دیگر دوباره تلاش کنید."
)


def _optional_text(value: Optional[str]) -> Optional[str]:
    """Normalize an optional field to ``None`` when blank or absent."""
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _resolve_employer_name(db: Session, employer_code: Optional[str]) -> Optional[str]:
    """Look up an employer's display name for the response only.

    ``employer_code`` is informational, not a foreign key (see
    ``models.trustee_payments``), so a code matching no active employer is
    not an error -- it is simply left unresolved.
    """
    if not employer_code:
        return None
    employer = (
        db.query(Employer)
        .filter(
            Employer.classification_code == employer_code,
            Employer.is_deleted == False,
        )
        .first()
    )
    return employer.name if employer else None


@router.post("/", response_model=TrusteePaymentCreateResponse, status_code=201)
def create_trustee_payment(
    payload: TrusteePaymentCreate,
    db: Session = Depends(get_db),
):
    """Register a new trustee (امانی) payment.

    Unlike ``POST /payments/draft``, this performs no balance validation and
    tolerates a ``contract_tracking_code``/``employer_code`` that matches
    nothing in ``contracts``/``employers`` -- the source reconciliation data
    is not guaranteed to reference records that exist in this system.
    """
    existing = (
        db.query(TrusteePayment.id)
        .filter(
            TrusteePayment.tracking_code == payload.tracking_code,
            TrusteePayment.is_deleted == False,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری '{payload.tracking_code}' قبلاً در سیستم "
                "پرداخت‌های امانی ثبت شده است."
            ),
        )

    try:
        trustee_payment = TrusteePayment(
            tracking_code=payload.tracking_code,
            contract_tracking_code=_optional_text(payload.contract_tracking_code),
            employer_code=_optional_text(payload.employer_code),
            amount=payload.amount,
            payment_year=payload.payment_year,
            notification_letter_number=_optional_text(payload.notification_letter_number),
            notification_date=payload.notification_date,
            source_note=_optional_text(payload.source_note),
            is_deleted=False,
        )
        db.add(trustee_payment)
        db.commit()
        db.refresh(trustee_payment)
    except IntegrityError as exc:
        db.rollback()
        logger.exception(
            "Integrity error while persisting trustee payment '%s': %s",
            payload.tracking_code,
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail=f"خطا: کد رهگیری '{payload.tracking_code}' قبلاً ثبت شده است.",
        ) from exc
    except DataError as exc:
        db.rollback()
        logger.exception(
            "Data error while persisting trustee payment '%s': %s",
            payload.tracking_code,
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail="نوع یا طول داده‌های ارسالی نامعتبر است.",
        ) from exc
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        logger.error(
            "Database connection failure while persisting trustee payment '%s': %s",
            payload.tracking_code,
            exc,
        )
        raise HTTPException(
            status_code=503, detail=CONNECTION_ERROR_MESSAGE
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(
            "Unexpected error while persisting trustee payment '%s': %s",
            payload.tracking_code,
            exc,
        )
        raise HTTPException(
            status_code=500, detail="خطا در ذخیره پرداخت امانی. لطفاً مجدداً تلاش کنید."
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(
            "Unexpected error while persisting trustee payment '%s': %s",
            payload.tracking_code,
            exc,
        )
        raise HTTPException(
            status_code=500, detail="خطا در ذخیره پرداخت امانی. لطفاً مجدداً تلاش کنید."
        ) from exc

    return TrusteePaymentCreateResponse(
        id=trustee_payment.id,
        tracking_code=trustee_payment.tracking_code,
        contract_tracking_code=trustee_payment.contract_tracking_code,
        employer_code=trustee_payment.employer_code,
        employer_name=_resolve_employer_name(db, trustee_payment.employer_code),
        amount=int(trustee_payment.amount),
        payment_year=trustee_payment.payment_year,
        notification_letter_number=trustee_payment.notification_letter_number,
        notification_date=trustee_payment.notification_date,
        source_note=trustee_payment.source_note,
        message="پرداخت امانی با موفقیت ثبت شد.",
    )
