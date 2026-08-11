"""Employer deposit receipt registration endpoints for the SATE financial system."""

import logging
import re
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import DataError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from core.database import get_db
from models.deposits import DepositReceipt
from models.employer import Employer
from schemas.deposit_schema import (
    DepositReceiptCreateResponse,
    EmployerBalancesResponse,
    YearBalance,
)
from services.financial_engine import calculate_real_balance

router = APIRouter(prefix="/deposits", tags=["Deposits"])
logger = logging.getLogger(__name__)

TARGET_BALANCE_YEARS = (1402, 1404, 1405)
ALLOWED_RECEIPT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEPOSIT_ARCHIVE_DIR = PROJECT_ROOT / "data" / "Archive" / "Deposits"

DEPOSIT_CONNECTION_ERROR_MESSAGE = (
    "خطا در ارتباط با پایگاه داده. لطفاً چند لحظه دیگر دوباره تلاش کنید."
)


def _optional_text(value: Optional[str]) -> Optional[str]:
    """Normalize an optional form field to ``None`` when blank or absent."""
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _get_active_employer(db: Session, employer_code: str) -> Employer:
    """Fetch an active (non-deleted) employer or raise a 404."""
    employer = (
        db.query(Employer)
        .filter(
            Employer.classification_code == employer_code,
            Employer.is_deleted == False,
        )
        .first()
    )
    if employer is None:
        raise HTTPException(
            status_code=404,
            detail=f"کارفرمای با کد '{employer_code}' یافت نشد یا حذف شده است.",
        )
    return employer


def _safe_filename(original_name: str) -> str:
    """Create a collision-resistant filename without unsafe path characters."""
    original_path = Path(original_name)
    extension = original_path.suffix.lower()
    sanitized_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", original_path.stem).strip("_")
    safe_stem = sanitized_stem[:80] or "deposit"
    return f"{safe_stem}_{uuid4().hex}{extension}"


def _save_receipt_file(file: UploadFile) -> str:
    """Persist an uploaded receipt to the deposit archive and return its relative path."""
    extension = Path(file.filename or "").suffix.lower().lstrip(".")
    if extension not in ALLOWED_RECEIPT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="نوع فایل نامعتبر است. فقط PDF، JPG و PNG مجاز هستند.",
        )

    DEPOSIT_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    destination = DEPOSIT_ARCHIVE_DIR / _safe_filename(file.filename)
    destination.write_bytes(file.file.read())
    return destination.relative_to(PROJECT_ROOT).as_posix()


def _delete_receipt_file(relative_path: str | None) -> None:
    """Remove a saved receipt file after a failed database write."""
    if not relative_path:
        return
    absolute_path = (PROJECT_ROOT / relative_path).resolve()
    archive_root = DEPOSIT_ARCHIVE_DIR.resolve()
    if archive_root not in absolute_path.parents:
        return
    absolute_path.unlink(missing_ok=True)


@router.get("/balances/{employer_code}", response_model=EmployerBalancesResponse)
def get_employer_balances(employer_code: str, db: Session = Depends(get_db)):
    """Return the employer's real balance for each configured target fiscal year.

    Balance formula: ``(Deposits + Transfers In) - (Payments + Transfers Out)``,
    computed per year via :func:`services.financial_engine.calculate_real_balance`.
    """
    _get_active_employer(db, employer_code)

    try:
        balances = [
            YearBalance(
                fiscal_year=year,
                balance=calculate_real_balance(db, employer_code, year),
            )
            for year in TARGET_BALANCE_YEARS
        ]
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(
            "Failed to compute balances for employer '%s': %s", employer_code, exc
        )
        raise HTTPException(
            status_code=500, detail="خطا در محاسبه مانده مالی کارفرما."
        ) from exc

    return EmployerBalancesResponse(employer_code=employer_code, balances=balances)


@router.post("/", response_model=DepositReceiptCreateResponse, status_code=201)
def create_deposit_receipt(
    employer_code: str = Form(..., description="Employer classification code"),
    fiscal_year: int = Form(..., ge=1300, le=1500, description="Target fiscal year"),
    deposit_amount: int = Form(..., gt=0, description="Deposit amount in whole Rials"),
    description: Optional[str] = Form(
        None, description="Optional deposit description/title (شرح/عنوان واریز)"
    ),
    file: UploadFile = File(..., description="Deposit receipt document"),
    db: Session = Depends(get_db),
):
    """Register a new physical deposit receipt for an employer.

    The receipt file is saved to the archive before the database write so a
    failed insert can clean it up, keeping the two in sync without leaving
    orphaned files or dangling attachment references.
    """
    employer = _get_active_employer(db, employer_code)
    attachment_path = _save_receipt_file(file)

    try:
        receipt = DepositReceipt(
            employer_code=employer_code,
            fiscal_year=fiscal_year,
            deposit_amount=deposit_amount,
            attachment_path=attachment_path,
            description=_optional_text(description),
            is_deleted=False,
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
    except IntegrityError as exc:
        db.rollback()
        _delete_receipt_file(attachment_path)
        logger.exception(
            "Integrity error while persisting deposit for '%s': %s",
            employer_code,
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail="خطای یکپارچگی اطلاعات هنگام ثبت واریزی.",
        ) from exc
    except DataError as exc:
        db.rollback()
        _delete_receipt_file(attachment_path)
        logger.exception(
            "Data error while persisting deposit for '%s': %s", employer_code, exc
        )
        raise HTTPException(
            status_code=400,
            detail="نوع یا طول داده‌های ارسالی نامعتبر است.",
        ) from exc
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        _delete_receipt_file(attachment_path)
        logger.error(
            "Database connection failure while persisting deposit for '%s': %s",
            employer_code,
            exc,
        )
        raise HTTPException(
            status_code=503, detail=DEPOSIT_CONNECTION_ERROR_MESSAGE
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        _delete_receipt_file(attachment_path)
        logger.error(
            "Unexpected error while persisting deposit for '%s': %s",
            employer_code,
            exc,
        )
        raise HTTPException(
            status_code=500, detail="خطا در ذخیره واریزی. لطفاً مجدداً تلاش کنید."
        ) from exc
    except Exception as exc:
        db.rollback()
        _delete_receipt_file(attachment_path)
        logger.error(
            "Unexpected error while persisting deposit for '%s': %s",
            employer_code,
            exc,
        )
        raise HTTPException(
            status_code=500, detail="خطا در ذخیره واریزی. لطفاً مجدداً تلاش کنید."
        ) from exc

    return DepositReceiptCreateResponse(
        id=receipt.id,
        employer_code=receipt.employer_code,
        employer_name=employer.name,
        fiscal_year=receipt.fiscal_year,
        deposit_amount=int(receipt.deposit_amount),
        attachment_path=receipt.attachment_path,
        description=receipt.description,
        message="واریزی با موفقیت ثبت شد.",
    )
