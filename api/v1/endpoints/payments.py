from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query as SAQuery
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.payment import Payment
from models.university import University
from schemas.payment_schema import (
    DraftDeleteResponse,
    FinalizeBatchRequest,
    FinalizeBatchResponse,
    PaymentDraftCreate,
    PaymentDraftCreateResponse,
    PaymentDraftResponse,
    PaymentValidationRequest,
    PaymentValidationResponse,
)
from services.financial_engine import (
    InsufficientFundsError,
    calculate_real_balance,
    validate_payment_impact,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post("/validate", response_model=PaymentValidationResponse)
def validate_payment(
    request: PaymentValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate the impact of a payment on the employer's balance without registering it.

    **Business Rule (updated):** negative balances are a hard block, not a
    warning — a payment that would take the employer's balance below zero
    returns HTTP 400, not HTTP 200 with a warning message. This mirrors the
    same check ``POST /payments/draft`` performs before staging a draft.

    **Parameters:**
    - `contract_tracking_code`: The contract tracking code
    - `amount`: The payment amount to validate
    - `funding_year`: The funding year for the payment

    **Returns:**
    - Current balance and projected balance for an affordable payment.
    """
    try:
        validation_result = validate_payment_impact(
            db=db,
            contract_code=request.contract_tracking_code,
            payment_amount=request.amount,
            funding_year=request.funding_year,
            lock_rows=True,
        )
        db.rollback()  # Read-only check: release the row locks immediately.
    except InsufficientFundsError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error validating payment: {str(exc)}"
        )

    return PaymentValidationResponse(
        employer_code=validation_result["employer_code"],
        current_balance=validation_result["current_balance"],
        payment_amount=validation_result["payment_amount"],
        new_balance=validation_result["new_balance"],
        is_negative=False,
        warning_message=None,
    )


def _enriched_payment_query(db: Session) -> SAQuery:
    """Build the shared Payment+Contract+Employer+University join.

    Every join is on a single FK to a single PK (Payment -> Contract is
    many-to-one, Contract -> Employer/University are each many-to-one), so
    this always returns exactly one row per ``Payment`` — no fan-out, no
    Cartesian product, and no N+1 (a single query regardless of row count).
    ``outerjoin`` is used throughout so a payment is still returned even if
    its contract or a downstream link is missing/soft-deleted-adjacent.
    """
    return (
        db.query(Payment, Contract, Employer, University)
        .outerjoin(
            Contract, Payment.contract_tracking_code == Contract.tracking_code
        )
        .outerjoin(
            Employer, Contract.employer_code == Employer.classification_code
        )
        .outerjoin(
            University, Contract.university_id == University.national_id
        )
    )


def _compute_balances_after(
    db: Session,
    rows: list[tuple[Payment, Contract, Employer, University]],
) -> dict[str, float]:
    """Compute each payment's employer balance immediately after it.

    ``calculate_real_balance`` already sums every ``Draft``/``Final``
    payment for an (employer, funding_year) pair, so it reflects the state
    *after all* of ``rows`` are applied. To show a distinct, meaningful
    "balance after this row" per row (not just the same final number
    repeated), payments are grouped by (employer_code, funding_year), the
    group's amounts are added back to get the balance *before* any of them,
    and a running balance is walked forward in tracking-code order.

    Only one ``calculate_real_balance`` call is made per distinct
    (employer_code, funding_year) pair present in ``rows`` — not one per
    row — regardless of how many payments share that pair.

    Returns:
        A ``{tracking_code: balance_after}`` map.
    """
    groups: dict[tuple[str, int], list[Payment]] = {}
    for payment, _contract, employer, _university in rows:
        if employer is None:
            continue
        key = (employer.classification_code, payment.funding_year)
        groups.setdefault(key, []).append(payment)

    balance_after: dict[str, float] = {}
    for (employer_code, funding_year), group_payments in groups.items():
        current_balance = calculate_real_balance(db, employer_code, funding_year)
        # current_balance already includes every payment in this group;
        # add them all back to recover the balance before any of them.
        running_balance = current_balance + sum(
            float(p.amount) for p in group_payments
        )
        for payment in sorted(group_payments, key=lambda p: p.tracking_code):
            running_balance -= float(payment.amount)
            balance_after[payment.tracking_code] = running_balance

    return balance_after


def _to_draft_response(
    payment: Payment,
    contract: Contract,
    employer: Employer,
    university: University,
    *,
    balance_after: float | None = None,
) -> PaymentDraftResponse:
    """Build the display-ready draft response from the joined entities."""
    return PaymentDraftResponse(
        tracking_code=payment.tracking_code,
        contract_tracking_code=payment.contract_tracking_code,
        contract_title=contract.title if contract else None,
        contract_total_amount=float(contract.total_amount) if contract else None,
        employer_code=employer.classification_code if employer else None,
        employer_name=employer.name if employer else None,
        university_name=university.name if university else None,
        amount=float(payment.amount),
        funding_year=payment.funding_year,
        payment_year=payment.payment_year,
        series=payment.series,
        status=payment.status,
        employer_balance_after=balance_after,
    )


@router.post("/draft", response_model=PaymentDraftCreateResponse, status_code=201)
def create_draft_payment(
    request: PaymentDraftCreate,
    db: Session = Depends(get_db),
):
    """
    Stage a single payment as a database-backed draft (batch-payment cart).

    Replaces the old in-memory ``st.session_state`` cart: drafts are
    persisted immediately, so they survive a browser reload, and their
    amount is reserved against the employer's real balance the instant
    they are created (``calculate_real_balance`` counts ``Draft`` rows
    alongside ``Final`` ones). A payment that would drive the balance
    negative is rejected outright with HTTP 400 — there is no warning-only
    path anymore.

    **Parameters:**
    - `tracking_code`: Unique payment tracking code (primary key).
    - `contract_tracking_code`: Contract the payment is drawn against.
    - `amount`: Payment amount in base Rials.
    - `funding_year`: Fiscal year the balance check and reservation apply to.
    - `payment_year`, `series`, `notification_letter_number`,
      `notification_date`: Optional metadata.

    **Returns:**
    - The created draft, HTTP 201, including `employer_balance_before` and
      `employer_balance_after` so the frontend can show the balance
      transition without a second API call.

    **Raises:**
    - `HTTPException(400)`: Duplicate tracking code, or insufficient funds.
    - `HTTPException(404)`: The contract or its employer is missing/deleted.
    """
    existing = (
        db.query(Payment.tracking_code)
        .filter(
            Payment.tracking_code == request.tracking_code,
            Payment.is_deleted == False,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{request.tracking_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )

    try:
        validation_result = validate_payment_impact(
            db=db,
            contract_code=request.contract_tracking_code,
            payment_amount=request.amount,
            funding_year=request.funding_year,
            lock_rows=True,
        )
    except InsufficientFundsError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))

    try:
        payment = Payment(
            tracking_code=request.tracking_code,
            contract_tracking_code=request.contract_tracking_code,
            amount=request.amount,
            funding_year=request.funding_year,
            payment_year=request.payment_year,
            series=request.series,
            notification_letter_number=request.notification_letter_number,
            notification_date=request.notification_date,
            status="Draft",
            is_deleted=False,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{request.tracking_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"خطا در ذخیره پیش‌نویس پرداخت: {exc}",
        )

    # Single joined round-trip for the display-ready contract/employer/
    # university fields, rather than one query per related entity.
    contract, employer, university = (
        db.query(Contract, Employer, University)
        .outerjoin(
            Employer, Contract.employer_code == Employer.classification_code
        )
        .outerjoin(
            University, Contract.university_id == University.national_id
        )
        .filter(Contract.tracking_code == payment.contract_tracking_code)
        .first()
    )

    base_response = _to_draft_response(
        payment,
        contract,
        employer,
        university,
        balance_after=validation_result["new_balance"],
    )
    return PaymentDraftCreateResponse(
        **base_response.model_dump(),
        employer_balance_before=validation_result["current_balance"],
    )


@router.get("/drafts", response_model=List[PaymentDraftResponse])
def list_draft_payments(
    series: Optional[str] = Query(
        None, description="Restrict results to a single payment series"
    ),
    db: Session = Depends(get_db),
):
    """Return every active draft payment, optionally filtered by series.

    Each row is enriched with its contract title/amount, employer name,
    university name, and a running ``employer_balance_after`` computed
    across the returned set (§ ``_compute_balances_after``) — all via one
    joined query plus one balance calculation per distinct employer/year
    pair, never one query per row.
    """
    query = _enriched_payment_query(db).filter(
        Payment.status == "Draft",
        Payment.is_deleted == False,
    )
    if series:
        query = query.filter(Payment.series == series)

    rows = query.order_by(Payment.tracking_code).all()
    balances_after = _compute_balances_after(db, rows)
    return [
        _to_draft_response(
            payment,
            contract,
            employer,
            university,
            balance_after=balances_after.get(payment.tracking_code),
        )
        for payment, contract, employer, university in rows
    ]


@router.delete("/draft/{tracking_code}", response_model=DraftDeleteResponse)
def delete_draft_payment(
    tracking_code: str,
    db: Session = Depends(get_db),
):
    """
    Remove one draft payment (soft-delete, per the system-wide rule).

    Only ``Draft``-status rows can be removed this way; a ``Final``
    payment is not touched by this endpoint even if the tracking code
    matches.
    """
    draft = (
        db.query(Payment)
        .filter(
            Payment.tracking_code == tracking_code,
            Payment.status == "Draft",
            Payment.is_deleted == False,
        )
        .first()
    )
    if draft is None:
        raise HTTPException(
            status_code=404,
            detail=f"پیش‌نویس پرداخت با کد رهگیری '{tracking_code}' یافت نشد.",
        )

    draft.is_deleted = True
    db.commit()

    return DraftDeleteResponse(
        message="پیش‌نویس با موفقیت حذف شد.",
        tracking_code=tracking_code,
    )


@router.post("/finalize-batch", response_model=FinalizeBatchResponse)
def finalize_batch(
    request: FinalizeBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm every active draft in a series, moving it to ``Final`` status.

    Purely a status transition: ``calculate_real_balance`` already counts
    ``Draft`` and ``Final`` payments identically, so finalizing a series
    does not change any employer's projected balance — the funds were
    already reserved the moment each draft was created. Finalizing a
    series with no matching drafts succeeds with ``finalized_count: 0``
    rather than erroring, so a duplicate click is harmless.

    Returns the full enriched records for the finalized batch (not just
    the count), so the frontend can build an Excel export from the
    response alone without a follow-up ``GET`` call.
    """
    try:
        drafts = (
            db.query(Payment)
            .filter(
                Payment.series == request.series,
                Payment.status == "Draft",
                Payment.is_deleted == False,
            )
            .all()
        )
        finalized_tracking_codes = [draft.tracking_code for draft in drafts]
        for draft in drafts:
            draft.status = "Final"
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"خطا در نهایی‌سازی لیست پرداخت: {exc}",
        )

    finalized_payments: List[PaymentDraftResponse] = []
    if finalized_tracking_codes:
        rows = (
            _enriched_payment_query(db)
            .filter(Payment.tracking_code.in_(finalized_tracking_codes))
            .order_by(Payment.tracking_code)
            .all()
        )
        balances_after = _compute_balances_after(db, rows)
        finalized_payments = [
            _to_draft_response(
                payment,
                contract,
                employer,
                university,
                balance_after=balances_after.get(payment.tracking_code),
            )
            for payment, contract, employer, university in rows
        ]

    return FinalizeBatchResponse(
        message=(
            f"{len(drafts)} پرداخت با موفقیت نهایی شد."
            if drafts
            else "هیچ پیش‌نویس فعالی برای این سری یافت نشد."
        ),
        series=request.series,
        finalized_count=len(drafts),
        finalized_payments=finalized_payments,
    )
