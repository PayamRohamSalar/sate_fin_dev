from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.payment import Payment
from schemas.payment_schema import (
    PaymentBatchValidationRequest,
    PaymentBatchValidationResponse,
    PaymentBulkCreate,
    PaymentBulkCreateResponse,
    PaymentValidationRequest,
    PaymentValidationResponse,
)
from services.financial_engine import (
    calculate_real_balance,
    lock_active_contract_and_employer,
    lock_active_contracts,
    lock_active_employers,
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
    Validate the impact of a payment on the employer's balance before registration.
    
    This endpoint implements FR-18, FR-19, FR-20:
    - Finds the employer linked to the contract
    - Calculates current and projected balance
    - Warns if balance becomes negative (but does not block the operation)
    
    **Business Rule:** This endpoint returns HTTP 200 even if the balance becomes negative,
    as the system is designed to warn but not prevent negative balances.
    
    **Parameters:**
    - `contract_tracking_code`: The contract tracking code
    - `amount`: The payment amount to validate
    - `funding_year`: The funding year for the payment
    
    **Returns:**
    - Current balance, new balance, and warning message if applicable
    """
    
    try:
        # Call the financial engine to validate payment impact
        validation_result = validate_payment_impact(
            db=db,
            contract_code=request.contract_tracking_code,
            payment_amount=request.amount,
            funding_year=request.funding_year,
            lock_rows=True,
        )
        
        # Prepare warning message if balance becomes negative
        warning_message = None
        if validation_result["is_negative"]:
            warning_message = "هشدار: ثبت این پرداخت باعث منفی شدن مانده حساب کارفرما خواهد شد"
        
        # Build and return response
        return PaymentValidationResponse(
            employer_code=validation_result["employer_code"],
            current_balance=validation_result["current_balance"],
            payment_amount=validation_result["payment_amount"],
            new_balance=validation_result["new_balance"],
            is_negative=validation_result["is_negative"],
            warning_message=warning_message
        )
        
    except ValueError as e:
        # Contract not found or deleted
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected error during validation
        raise HTTPException(
            status_code=500,
            detail=f"Error validating payment: {str(e)}"
        )


@router.post("/validate-draft", response_model=PaymentBatchValidationResponse)
def validate_draft_payment(
    request: PaymentBatchValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validate a single drafted (cart) payment against the employer's balance.

    The available balance is computed as the current database balance minus the
    `pending_cart_amount` (other drafts already reserved in the frontend cart
    for the same employer). If the payment amount exceeds the available balance,
    the request is rejected with HTTP 400 and the exact remaining balance.

    **Parameters:**
    - `contract_tracking_code`: Contract linked to the drafted payment.
    - `amount`: Amount of the drafted payment.
    - `funding_year`: Funding (budget consumption) year.
    - `pending_cart_amount`: Sum of other drafts for the same employer in the cart.

    **Returns:**
    - HTTP 200 with balance breakdown when the draft is affordable.
    - HTTP 400 with the remaining balance when funds are insufficient.
    """
    try:
        contract, _ = lock_active_contract_and_employer(
            db, request.contract_tracking_code
        )
        current_db_balance = calculate_real_balance(
            db, contract.employer_code, request.funding_year
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating balance: {str(exc)}",
        )

    available_balance = current_db_balance - request.pending_cart_amount

    if available_balance < request.amount:
        raise HTTPException(
            status_code=400,
            detail=(
                "Insufficient funds for this draft payment. "
                f"Remaining available balance is {available_balance:,.0f} Rials, "
                f"but the requested amount is {request.amount:,.0f} Rials."
            ),
        )

    return PaymentBatchValidationResponse(
        employer_code=contract.employer_code,
        current_db_balance=current_db_balance,
        pending_cart_amount=request.pending_cart_amount,
        available_balance=available_balance,
        amount=request.amount,
        remaining_balance=available_balance - request.amount,
        is_valid=True,
    )


@router.post("/bulk-submit", response_model=PaymentBulkCreateResponse, status_code=201)
def bulk_submit_payments(
    request: PaymentBulkCreate,
    db: Session = Depends(get_db),
):
    """
    Register a payment batch in one pessimistically locked transaction.

    Active contract and employer rows are locked with PostgreSQL ``FOR UPDATE``
    before balances are calculated. Locks are acquired in deterministic order
    and held through all inserts and the commit. Negative balances do not block
    or roll back registration; they are returned as FR-20 warning messages.

    Args:
        request: Validated batch of payments to register atomically.
        db: Active SQLAlchemy database session.

    Returns:
        The committed tracking codes and any negative-balance warnings.

    Raises:
        HTTPException: If identifiers are duplicated, missing, or soft-deleted,
            or if the database transaction fails.
    """
    tracking_codes = [item.tracking_code for item in request.payments]
    seen_codes: set[str] = set()
    duplicate_request_code = None
    for tracking_code in tracking_codes:
        if tracking_code in seen_codes:
            duplicate_request_code = tracking_code
            break
        seen_codes.add(tracking_code)

    if duplicate_request_code is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{duplicate_request_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )

    running_balances: dict[tuple[str, int], float] = {}
    created_tracking_codes: List[str] = []
    warning_messages: List[str] = []

    try:
        existing = (
            db.query(Payment.tracking_code)
            .filter(
                Payment.tracking_code.in_(tracking_codes),
                Payment.is_deleted == False,
            )
            .first()
        )
        if existing:
            duplicate_code = existing[0]
            raise HTTPException(
                status_code=400,
                detail=(
                    f"خطا: کد رهگیری پرداخت '{duplicate_code}' "
                    "قبلاً در سیستم ثبت شده است."
                ),
            )

        contract_codes = [
            item.contract_tracking_code for item in request.payments
        ]
        locked_contracts = lock_active_contracts(db, contract_codes)
        missing_contract_codes = sorted(
            set(contract_codes) - set(locked_contracts)
        )
        if missing_contract_codes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Contract '{missing_contract_codes[0]}' not found or "
                    "has been deleted."
                ),
            )

        employer_codes = [
            contract.employer_code for contract in locked_contracts.values()
        ]
        locked_employers = lock_active_employers(db, employer_codes)
        missing_employer_codes = sorted(
            set(employer_codes) - set(locked_employers)
        )
        if missing_employer_codes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Employer '{missing_employer_codes[0]}' not found or "
                    "has been deleted."
                ),
            )

        for index, item in enumerate(request.payments):
            contract = locked_contracts[item.contract_tracking_code]
            balance_key = (contract.employer_code, item.funding_year)
            if balance_key not in running_balances:
                running_balances[balance_key] = calculate_real_balance(
                    db, contract.employer_code, item.funding_year
                )

            payment = Payment(
                tracking_code=item.tracking_code,
                contract_tracking_code=item.contract_tracking_code,
                series=item.series,
                amount=item.amount,
                notification_letter_number=item.notification_letter_number,
                notification_date=item.notification_date,
                payment_year=item.payment_year,
                funding_year=item.funding_year,
                attachment_path=item.attachment_path,
                is_deleted=False,
            )
            db.add(payment)

            running_balances[balance_key] -= item.amount
            if running_balances[balance_key] < 0:
                warning_messages.append(
                    f"Row {index + 1} (tracking code '{item.tracking_code}'): "
                    f"employer '{contract.employer_code}' balance for funding "
                    f"year {item.funding_year} is negative "
                    f"({running_balances[balance_key]:,.0f} Rials) after registration."
                )
            created_tracking_codes.append(item.tracking_code)

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error during bulk submission (transaction rolled back): {str(exc)}",
        )

    return PaymentBulkCreateResponse(
        message=(
            "All payments were registered successfully with balance warnings."
            if warning_messages
            else "All payments were registered successfully."
        ),
        submitted_count=len(created_tracking_codes),
        tracking_codes=created_tracking_codes,
        warning_messages=warning_messages,
    )
