from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from services.financial_engine import validate_payment_impact
from schemas.payment_schema import PaymentValidationRequest, PaymentValidationResponse

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
