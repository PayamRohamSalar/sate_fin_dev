from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.payment import Payment
from services.financial_engine import calculate_real_balance, validate_payment_impact
from schemas.payment_schema import (
    PaymentBatchValidationRequest,
    PaymentBatchValidationResponse,
    PaymentBulkCreate,
    PaymentBulkCreateResponse,
    PaymentValidationRequest,
    PaymentValidationResponse,
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
            funding_year=request.funding_year
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
    contract = db.query(Contract).filter(
        Contract.tracking_code == request.contract_tracking_code,
        Contract.is_deleted == False,
    ).first()

    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract with tracking code '{request.contract_tracking_code}' not found or has been deleted.",
        )

    try:
        current_db_balance = calculate_real_balance(
            db, contract.employer_code, request.funding_year
        )
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


@router.post("/bulk-submit", response_model=PaymentBulkCreateResponse)
def bulk_submit_payments(
    request: PaymentBulkCreate,
    db: Session = Depends(get_db),
):
    """
    Register a batch (cart) of payments inside a single database transaction.

    The endpoint iterates through the submitted payments and recalculates a
    running balance per employer/funding-year dynamically. Each payment reserves
    part of the available balance so that later payments in the same batch see
    the reduced balance. If any payment breaches the available balance, the
    ENTIRE transaction is rolled back and an HTTP 400 identifies the failing row.

    **Parameters:**
    - `payments`: List of payment objects to register atomically.

    **Returns:**
    - HTTP 200 with the committed count and tracking codes when all succeed.
    - HTTP 400 (rolled back) identifying the contract/row that failed.
    """
    tracking_codes = [item.tracking_code for item in request.payments]

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
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{duplicate_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )

    running_balances: dict = {}
    created_tracking_codes: List[str] = []

    try:
        for index, item in enumerate(request.payments):
            contract = db.query(Contract).filter(
                Contract.tracking_code == item.contract_tracking_code,
                Contract.is_deleted == False,
            ).first()

            if not contract:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Row {index + 1} (tracking code '{item.tracking_code}') failed: "
                        f"contract '{item.contract_tracking_code}' not found or has been deleted."
                    ),
                )

            balance_key = (contract.employer_code, item.funding_year)
            if balance_key not in running_balances:
                running_balances[balance_key] = calculate_real_balance(
                    db, contract.employer_code, item.funding_year
                )

            if running_balances[balance_key] < item.amount:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Row {index + 1} (tracking code '{item.tracking_code}', "
                        f"contract '{item.contract_tracking_code}') failed: insufficient funds. "
                        f"Remaining balance is {running_balances[balance_key]:,.0f} Rials, "
                        f"but the requested amount is {item.amount:,.0f} Rials."
                    ),
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
        message="All payments were registered successfully.",
        submitted_count=len(created_tracking_codes),
        tracking_codes=created_tracking_codes,
    )
