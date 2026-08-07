import logging
import traceback
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.exc import (
    DataError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.researchers import Researcher
from models.university import University
from schemas.contract_schema import (
    ContractCreate,
    ContractDetail,
    ContractSearchResult,
    ContractUpdate,
)

router = APIRouter(prefix="/contracts", tags=["Contracts"])
logger = logging.getLogger(__name__)

DUPLICATE_CONTRACT_MESSAGE = "کد رهگیری تکراری است."
CONTRACT_DATA_MISMATCH_MESSAGE = (
    "خطای یکپارچگی اطلاعات: کارفرما، دانشگاه یا فناور نامعتبر است."
)
CONTRACT_DATA_FORMAT_MESSAGE = (
    "نوع یا طول داده‌های ارسالی نامعتبر است (مثلا فرمت تاریخ یا مبالغ)."
)
CONTRACT_CONNECTION_ERROR_MESSAGE = (
    "خطا در ارتباط با پایگاه داده. لطفاً چند لحظه دیگر دوباره تلاش کنید."
)
ALLOWED_CONTRACT_EMPLOYER_TYPES = {"Mother", "Independent"}


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values before database persistence."""
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _is_unique_violation(error: IntegrityError) -> bool:
    """Return whether an integrity error represents a unique-key conflict."""
    original_error = error.orig
    sqlstate = getattr(original_error, "sqlstate", None) or getattr(
        original_error, "pgcode", None
    )
    if sqlstate == "23505":
        return True

    return "unique constraint" in str(original_error).lower()


def _is_foreign_key_violation(error: IntegrityError) -> bool:
    """Return whether an integrity error represents a foreign-key conflict."""
    original_error = error.orig
    sqlstate = getattr(original_error, "sqlstate", None) or getattr(
        original_error, "pgcode", None
    )
    if sqlstate == "23503":
        return True

    return "foreign key" in str(original_error).lower()


def _raise_contract_persistence_error(
    error: SQLAlchemyError,
    tracking_code: str,
) -> None:
    """Map a failed contract write to a localized API error."""
    logger.exception("Failed to persist contract '%s': %s", tracking_code, error)

    if isinstance(error, IntegrityError) and _is_unique_violation(error):
        raise HTTPException(
            status_code=409,
            detail=DUPLICATE_CONTRACT_MESSAGE.format(tracking_code=tracking_code),
        ) from error

    if isinstance(error, IntegrityError) and _is_foreign_key_violation(error):
        raise HTTPException(
            status_code=400,
            detail=CONTRACT_DATA_MISMATCH_MESSAGE,
        ) from error

    if isinstance(error, DataError):
        raise HTTPException(
            status_code=400,
            detail=CONTRACT_DATA_FORMAT_MESSAGE,
        ) from error

    raise HTTPException(
        status_code=400,
        detail=CONTRACT_DATA_MISMATCH_MESSAGE,
    ) from error


def _raise_contract_connection_error(
    error: Exception,
    tracking_code: str,
) -> None:
    """Log a database connectivity failure and return a retryable 503 error.

    Handles both SQLAlchemy's wrapped ``OperationalError`` and a raw
    ``ConnectionResetError`` that may surface if the connection drops before
    the driver wraps it, so a mid-request network failure never escapes as an
    unhandled exception.
    """
    logger.error(
        "Database connection failure while persisting contract '%s': %s",
        tracking_code,
        error,
    )
    raise HTTPException(
        status_code=503,
        detail=CONTRACT_CONNECTION_ERROR_MESSAGE,
    ) from error


def _raise_unexpected_contract_error(
    error: Exception,
    tracking_code: str,
) -> None:
    """Log an unexpected contract failure and return a safe server error."""
    logger.error(
        "Unexpected contract persistence error for '%s': %s",
        tracking_code,
        error,
    )
    print(traceback.format_exc())
    raise HTTPException(
        status_code=500,
        detail="خطا در ذخیره قرارداد. لطفاً مجدداً تلاش کنید.",
    ) from error


def _get_active_contract_parties(
    db: Session,
    payload: ContractCreate | ContractUpdate,
) -> tuple[Employer, University, Researcher]:
    """Load active contract parties and enforce employer business rules.

    Shared by both contract creation and contract update, since
    ``ContractCreate`` and ``ContractUpdate`` expose identical
    employer/university/researcher fields.
    """
    employer = (
        db.query(Employer)
        .filter(
            Employer.classification_code
            == payload.employer_classification_code,
            Employer.is_deleted == False,
        )
        .first()
    )
    if employer is None:
        raise HTTPException(
            status_code=404,
            detail="کارفرمای انتخاب‌شده یافت نشد یا حذف شده است.",
        )
    if employer.employer_type not in ALLOWED_CONTRACT_EMPLOYER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "خطا: قرارداد فقط باید به نام شرکت مادر یا مستقل ثبت شود."
            ),
        )

    university = (
        db.query(University)
        .filter(
            University.national_id == payload.university_national_id,
            University.is_deleted == False,
        )
        .first()
    )
    if university is None:
        raise HTTPException(
            status_code=404,
            detail="دانشگاه انتخاب‌شده یافت نشد یا حذف شده است.",
        )

    researcher = (
        db.query(Researcher)
        .filter(
            Researcher.national_code == payload.researcher_national_id,
            Researcher.is_deleted == False,
        )
        .first()
    )
    if researcher is None:
        raise HTTPException(
            status_code=404,
            detail="فناور انتخاب‌شده یافت نشد یا حذف شده است.",
        )

    return employer, university, researcher


def _to_search_result(
    contract: Contract,
    employer: Employer,
    university: University,
    researcher: Researcher,
) -> ContractSearchResult:
    """Build the public contract response from persisted entities."""
    return ContractSearchResult(
        contract_tracking_code=contract.tracking_code,
        title=contract.title,
        employer_name=employer.name,
        employer_classification_code=employer.classification_code,
        university_name=university.name,
        researcher_name=researcher.full_name,
    )


@router.get("/search", response_model=List[ContractSearchResult])
def search_contracts(
    q: str = Query(
        ...,
        min_length=1,
        description="Search term matched against tracking code or title",
    ),
    db: Session = Depends(get_db),
):
    """Search active contracts and active related entities for auto-fill."""
    like_pattern = f"%{q}%"
    rows = (
        db.query(
            Contract.tracking_code.label("contract_tracking_code"),
            Contract.title.label("title"),
            Employer.name.label("employer_name"),
            Employer.classification_code.label(
                "employer_classification_code"
            ),
            University.name.label("university_name"),
            Researcher.full_name.label("researcher_name"),
        )
        .join(
            Employer,
            and_(
                Contract.employer_code == Employer.classification_code,
                Employer.is_deleted == False,
            ),
        )
        .join(
            University,
            and_(
                Contract.university_id == University.national_id,
                University.is_deleted == False,
            ),
        )
        .join(
            Researcher,
            and_(
                Contract.researcher_id == Researcher.national_code,
                Researcher.is_deleted == False,
            ),
        )
        .filter(
            Contract.is_deleted == False,
            or_(
                Contract.tracking_code.ilike(like_pattern),
                Contract.title.ilike(like_pattern),
            ),
        )
        .all()
    )

    return [ContractSearchResult(**row._asdict()) for row in rows]


@router.post("/", response_model=ContractSearchResult, status_code=201)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
):
    """Register a contract, keeping the full lookup-and-write flow inside one
    transaction-safe try/except so any failure — validation, persistence, or
    a dropped database connection — rolls back cleanly and returns a proper
    HTTP error instead of an unhandled exception.
    """
    tracking_code = payload.tracking_code.strip()
    title = payload.title.strip()
    if not tracking_code or not title:
        raise HTTPException(
            status_code=400,
            detail="کد رهگیری و عنوان قرارداد الزامی هستند.",
        )

    try:
        existing_contract = (
            db.query(Contract.tracking_code)
            .filter(
                Contract.tracking_code == tracking_code,
                Contract.is_deleted == False,
            )
            .first()
        )
        if existing_contract is not None:
            raise HTTPException(
                status_code=409,
                detail=DUPLICATE_CONTRACT_MESSAGE.format(
                    tracking_code=tracking_code
                ),
            )

        employer, university, researcher = _get_active_contract_parties(
            db, payload
        )
        contract_date: date = payload.contract_date
        contract = Contract(
            tracking_code=tracking_code,
            employer_code=payload.employer_classification_code,
            university_id=payload.university_national_id,
            researcher_id=payload.researcher_national_id,
            contract_number=_optional_text(payload.contract_number),
            proposal_id=_optional_text(payload.proposal_id),
            attachment_path=_optional_text(payload.attachment_path),
            title=title,
            total_amount=payload.total_amount,
            contract_date=contract_date,
            duration_months=payload.duration_months,
            status="فعال",
            is_deleted=False,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except DataError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        _raise_contract_connection_error(exc, tracking_code)
    except SQLAlchemyError as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)
    except Exception as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)

    return _to_search_result(contract, employer, university, researcher)


CONTRACT_NOT_FOUND_MESSAGE = "قرارداد یافت نشد یا حذف شده است."


def _get_active_contract_or_404(db: Session, tracking_code: str) -> Contract:
    """Fetch a non-soft-deleted contract by tracking code or raise a 404."""
    contract = (
        db.query(Contract)
        .filter(
            Contract.tracking_code == tracking_code,
            Contract.is_deleted == False,
        )
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail=CONTRACT_NOT_FOUND_MESSAGE)
    return contract


def _to_detail(contract: Contract) -> ContractDetail:
    """Build the full-detail response used to populate the edit form."""
    return ContractDetail(
        tracking_code=contract.tracking_code,
        employer_classification_code=contract.employer_code,
        university_national_id=contract.university_id,
        researcher_national_id=contract.researcher_id,
        contract_number=contract.contract_number,
        proposal_id=contract.proposal_id,
        attachment_path=contract.attachment_path,
        title=contract.title,
        total_amount=int(contract.total_amount),
        contract_date=contract.contract_date,
        duration_months=contract.duration_months,
        status=contract.status,
    )


@router.get("/{tracking_code}", response_model=ContractDetail)
def get_contract(
    tracking_code: str,
    db: Session = Depends(get_db),
):
    """Fetch the full details of a single active contract for editing."""
    contract = _get_active_contract_or_404(db, tracking_code)
    return _to_detail(contract)


@router.put("/{tracking_code}", response_model=ContractSearchResult)
def update_contract(
    tracking_code: str,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing active contract's editable fields.

    Reuses the same party-resolution/business-rule check, optional-text
    normalization, and layered error handling as :func:`create_contract` so
    an update is validated exactly as strictly as a fresh registration.
    """
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=400,
            detail="عنوان قرارداد الزامی است.",
        )

    try:
        contract = _get_active_contract_or_404(db, tracking_code)
        employer, university, researcher = _get_active_contract_parties(
            db, payload
        )

        contract.employer_code = payload.employer_classification_code
        contract.university_id = payload.university_national_id
        contract.researcher_id = payload.researcher_national_id
        contract.contract_number = _optional_text(payload.contract_number)
        contract.proposal_id = _optional_text(payload.proposal_id)
        contract.attachment_path = _optional_text(payload.attachment_path)
        contract.title = title
        contract.total_amount = payload.total_amount
        contract.contract_date = payload.contract_date
        contract.duration_months = payload.duration_months

        db.commit()
        db.refresh(contract)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except DataError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        _raise_contract_connection_error(exc, tracking_code)
    except SQLAlchemyError as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)
    except Exception as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)

    return _to_search_result(contract, employer, university, researcher)
