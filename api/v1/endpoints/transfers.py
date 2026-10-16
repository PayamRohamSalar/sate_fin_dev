"""Credit-transfer (انتقال اعتبار) endpoints for the SATE financial system.

Supports the report/edit/add dashboard page: a filterable list for the
report view, plus create and update endpoints for the entry/edit forms.
Unlike ``trustee_payments``, every foreign key here (``source_employer_code``,
``destination_employer_code``, ``contract_tracking_code``) is a real FK on
the ``credit_transfers`` table, so both endpoints validate the referenced
rows exist and are active before writing.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import DataError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, aliased

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.transfer import CreditTransfer
from schemas.transfer_schema import (
    CreditTransferCreate,
    CreditTransferResponse,
    CreditTransferUpdate,
)
from services.financial_engine import (
    calculate_combined_pool_balance,
    calculate_gross_pool_balance,
)

router = APIRouter(prefix="/credit-transfers", tags=["Credit Transfers"])
logger = logging.getLogger(__name__)

CONNECTION_ERROR_MESSAGE = (
    "خطا در ارتباط با پایگاه داده. لطفاً چند لحظه دیگر دوباره تلاش کنید."
)

SourceEmployer = aliased(Employer, name="source_employer")
DestinationEmployer = aliased(Employer, name="destination_employer")


def _optional_text(value: Optional[str]) -> Optional[str]:
    """Normalize an optional field to ``None`` when blank or absent."""
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _get_active_employer(db: Session, employer_code: str, *, role: str) -> Employer:
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
            detail=f"کارفرمای {role} با کد '{employer_code}' یافت نشد یا حذف شده است.",
        )
    return employer


def _check_combined_balance(
    db: Session, source_employer_code: str, amount: int, *, exclude_transfer_id: int | None = None
) -> None:
    """Reject a transfer that would exceed the source employer's combined
    1402+1404 balance (see ``calculate_combined_pool_balance`` for why this
    checks the combined pool instead of a single fiscal year).

    ``exclude_transfer_id`` lets an update re-validate without the transfer's
    own prior amount counting against itself.
    """
    available = calculate_combined_pool_balance(db, source_employer_code, lock_employer=True)
    if exclude_transfer_id is not None:
        prior = (
            db.query(CreditTransfer)
            .filter(CreditTransfer.id == exclude_transfer_id, CreditTransfer.is_deleted == False)  # noqa: E712
            .first()
        )
        if prior is not None and prior.source_employer_code == source_employer_code:
            available += float(prior.amount)
    if amount > available:
        raise HTTPException(
            status_code=400,
            detail=(
                f"مانده تجمیعی کارفرمای مبدأ (سال‌های ۱۴۰۲ و ۱۴۰۴ با هم) "
                f"{available:,.0f} ریال است؛ مبلغ انتقالی {amount:,.0f} ریال از آن بیشتر است."
            ),
        )


def _get_active_contract(db: Session, tracking_code: str) -> Contract:
    """Fetch an active (non-deleted) contract or raise a 404."""
    contract = (
        db.query(Contract)
        .filter(
            Contract.tracking_code == tracking_code,
            Contract.is_deleted == False,
        )
        .first()
    )
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail=f"قرارداد با کد '{tracking_code}' یافت نشد یا حذف شده است.",
        )
    return contract


def _enriched_transfer_query(db: Session):
    """Build the shared CreditTransfer+source/destination Employer+Contract join."""
    return (
        db.query(CreditTransfer, SourceEmployer, DestinationEmployer, Contract)
        .outerjoin(
            SourceEmployer,
            CreditTransfer.source_employer_code == SourceEmployer.classification_code,
        )
        .outerjoin(
            DestinationEmployer,
            CreditTransfer.destination_employer_code
            == DestinationEmployer.classification_code,
        )
        .outerjoin(
            Contract, CreditTransfer.contract_tracking_code == Contract.tracking_code
        )
    )


def _to_response(
    transfer: CreditTransfer,
    source_employer: Optional[Employer],
    destination_employer: Optional[Employer],
    contract: Optional[Contract],
) -> CreditTransferResponse:
    """Build the display-ready response from the joined entities."""
    return CreditTransferResponse(
        id=transfer.id,
        source_employer_code=transfer.source_employer_code,
        source_employer_name=source_employer.name if source_employer else None,
        destination_employer_code=transfer.destination_employer_code,
        destination_employer_name=(
            destination_employer.name if destination_employer else None
        ),
        contract_tracking_code=transfer.contract_tracking_code,
        contract_title=contract.title if contract else None,
        fiscal_year=transfer.fiscal_year,
        amount=int(transfer.amount),
        broker_name=transfer.broker_name,
        documentation=transfer.documentation,
    )


def _attach_report_balances(db: Session, responses: list[CreditTransferResponse]) -> None:
    """Fill the report-only enrichment fields on the list response.

    Computed once per distinct source employer / contract (not per row), and
    always over ALL active transfers -- the fiscal-year / employer filters
    narrow the rows shown, never the balances or the contract's funded total.
    """
    if not responses:
        return

    contract_codes = {r.contract_tracking_code for r in responses}
    contract_amounts = {
        code: float(amount)
        for code, amount in db.query(Contract.tracking_code, Contract.total_amount)
        .filter(Contract.tracking_code.in_(contract_codes))
        .all()
    }
    funded_totals = {
        code: float(total)
        for code, total in db.query(
            CreditTransfer.contract_tracking_code, func.sum(CreditTransfer.amount)
        )
        .filter(
            CreditTransfer.contract_tracking_code.in_(contract_codes),
            CreditTransfer.is_deleted == False,  # noqa: E712
        )
        .group_by(CreditTransfer.contract_tracking_code)
        .all()
    }

    source_codes = {r.source_employer_code for r in responses}
    gross = {code: calculate_gross_pool_balance(db, code) for code in source_codes}
    net = {code: calculate_combined_pool_balance(db, code) for code in source_codes}

    for r in responses:
        if r.contract_tracking_code in contract_amounts:
            r.contract_amount = int(contract_amounts[r.contract_tracking_code])
        r.contract_funded_total = int(funded_totals.get(r.contract_tracking_code, 0))
        r.source_balance_before_transfers = int(gross[r.source_employer_code])
        r.source_balance_after_transfers = int(net[r.source_employer_code])


@router.get("/", response_model=list[CreditTransferResponse])
def list_credit_transfers(
    fiscal_year: Optional[int] = Query(None, description="Restrict results to a single fiscal year"),
    employer_code: Optional[str] = Query(
        None, description="Restrict results to transfers where this employer is the source or destination"
    ),
    contract_tracking_code: Optional[str] = Query(
        None, description="Restrict results to a single contract"
    ),
    db: Session = Depends(get_db),
):
    """Return active credit transfers for the report/edit dashboard, newest first."""
    query = _enriched_transfer_query(db).filter(CreditTransfer.is_deleted == False)

    if fiscal_year is not None:
        query = query.filter(CreditTransfer.fiscal_year == fiscal_year)
    if employer_code:
        query = query.filter(
            (CreditTransfer.source_employer_code == employer_code)
            | (CreditTransfer.destination_employer_code == employer_code)
        )
    if contract_tracking_code:
        query = query.filter(
            CreditTransfer.contract_tracking_code == contract_tracking_code
        )

    rows = query.order_by(CreditTransfer.id.desc()).all()
    responses = [
        _to_response(transfer, source_employer, destination_employer, contract)
        for transfer, source_employer, destination_employer, contract in rows
    ]
    _attach_report_balances(db, responses)
    return responses


@router.post("/", response_model=CreditTransferResponse, status_code=201)
def create_credit_transfer(
    payload: CreditTransferCreate,
    db: Session = Depends(get_db),
):
    """Register a new credit transfer between two employers against a contract."""
    source_employer = _get_active_employer(
        db, payload.source_employer_code, role="مبدأ"
    )
    destination_employer = _get_active_employer(
        db, payload.destination_employer_code, role="مقصد"
    )
    contract = _get_active_contract(db, payload.contract_tracking_code)
    _check_combined_balance(db, source_employer.classification_code, payload.amount)

    try:
        transfer = CreditTransfer(
            source_employer_code=source_employer.classification_code,
            destination_employer_code=destination_employer.classification_code,
            contract_tracking_code=contract.tracking_code,
            fiscal_year=payload.fiscal_year,
            amount=payload.amount,
            broker_name=_optional_text(payload.broker_name),
            documentation=_optional_text(payload.documentation),
            is_deleted=False,
        )
        db.add(transfer)
        db.commit()
        db.refresh(transfer)
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Integrity error while persisting credit transfer: %s", exc)
        raise HTTPException(
            status_code=400, detail="خطای یکپارچگی اطلاعات هنگام ثبت انتقال اعتبار."
        ) from exc
    except DataError as exc:
        db.rollback()
        logger.exception("Data error while persisting credit transfer: %s", exc)
        raise HTTPException(
            status_code=400, detail="نوع یا طول داده‌های ارسالی نامعتبر است."
        ) from exc
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        logger.error(
            "Database connection failure while persisting credit transfer: %s", exc
        )
        raise HTTPException(status_code=503, detail=CONNECTION_ERROR_MESSAGE) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Unexpected error while persisting credit transfer: %s", exc)
        raise HTTPException(
            status_code=500, detail="خطا در ذخیره انتقال اعتبار. لطفاً مجدداً تلاش کنید."
        ) from exc

    return _to_response(transfer, source_employer, destination_employer, contract)


@router.put("/{transfer_id}", response_model=CreditTransferResponse)
def update_credit_transfer(
    transfer_id: int,
    payload: CreditTransferUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing active credit transfer's editable fields."""
    transfer = (
        db.query(CreditTransfer)
        .filter(CreditTransfer.id == transfer_id, CreditTransfer.is_deleted == False)
        .first()
    )
    if transfer is None:
        raise HTTPException(
            status_code=404,
            detail=f"انتقال اعتبار با شناسه '{transfer_id}' یافت نشد یا حذف شده است.",
        )

    source_employer = _get_active_employer(
        db, payload.source_employer_code, role="مبدأ"
    )
    destination_employer = _get_active_employer(
        db, payload.destination_employer_code, role="مقصد"
    )
    contract = _get_active_contract(db, payload.contract_tracking_code)
    _check_combined_balance(
        db, source_employer.classification_code, payload.amount, exclude_transfer_id=transfer_id
    )

    try:
        transfer.source_employer_code = source_employer.classification_code
        transfer.destination_employer_code = destination_employer.classification_code
        transfer.contract_tracking_code = contract.tracking_code
        transfer.fiscal_year = payload.fiscal_year
        transfer.amount = payload.amount
        transfer.broker_name = _optional_text(payload.broker_name)
        transfer.documentation = _optional_text(payload.documentation)

        db.commit()
        db.refresh(transfer)
    except IntegrityError as exc:
        db.rollback()
        logger.exception(
            "Integrity error while updating credit transfer '%s': %s", transfer_id, exc
        )
        raise HTTPException(
            status_code=400, detail="خطای یکپارچگی اطلاعات هنگام ویرایش انتقال اعتبار."
        ) from exc
    except DataError as exc:
        db.rollback()
        logger.exception(
            "Data error while updating credit transfer '%s': %s", transfer_id, exc
        )
        raise HTTPException(
            status_code=400, detail="نوع یا طول داده‌های ارسالی نامعتبر است."
        ) from exc
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        logger.error(
            "Database connection failure while updating credit transfer '%s': %s",
            transfer_id,
            exc,
        )
        raise HTTPException(status_code=503, detail=CONNECTION_ERROR_MESSAGE) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(
            "Unexpected error while updating credit transfer '%s': %s", transfer_id, exc
        )
        raise HTTPException(
            status_code=500, detail="خطا در ذخیره تغییرات. لطفاً مجدداً تلاش کنید."
        ) from exc

    return _to_response(transfer, source_employer, destination_employer, contract)
