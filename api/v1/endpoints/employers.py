from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from core.database import get_db
from services.financial_engine import calculate_real_balance
from schemas.employer_schema import BalanceResponse
from models.employer import Employer

router = APIRouter(
    prefix="/employers",
    tags=["Employers"]
)


@router.get("/{employer_id}/balance", response_model=BalanceResponse)
def get_employer_balance(
    employer_id: str = Path(..., description="Employer classification code"),
    funding_year: int = Query(..., description="Funding year (fiscal year) for balance calculation", ge=1300, le=1500),
    db: Session = Depends(get_db)
):
    """
    Calculate and return the real financial balance for a specific employer and funding year.

    The balance is calculated as:
    (Total Deposits + Transfers In) - (Total Payments + Transfers Out)

    Deposits include subsidiary receipts for Mother employers.
    
    **Parameters:**
    - `employer_id`: The employer's classification code
    - `funding_year`: The fiscal year for the balance calculation (Persian calendar year)
    
    **Returns:**
    - Employer code
    - Funding year
    - Total calculated balance
    - Current inquiry date in Jalali format
    """
    
    # Verify that the employer exists in the database
    employer = db.query(Employer).filter(
        Employer.classification_code == employer_id,
        Employer.is_deleted == False
    ).first()
    
    if not employer:
        raise HTTPException(
            status_code=404,
            detail=f"Employer with code '{employer_id}' not found or has been deleted."
        )
    
    # Calculate the real balance using the financial engine
    try:
        balance = calculate_real_balance(db, employer_id, funding_year)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating balance: {str(e)}"
        )
    
    # Return the response with current Jalali date
    return BalanceResponse(
        employer_code=employer_id,
        funding_year=funding_year,
        total_balance=balance,
        inquiry_date_jalali=BalanceResponse.get_current_jalali_date()
    )

@router.get("/lookup", summary="Employer lookup for dropdowns")
def employer_lookup(db: Session = Depends(get_db)):
    """Return classification_code + name for non-subsidiary employers."""
    rows = db.query(Employer.classification_code, Employer.name).filter(
        Employer.employer_type != "Subsidiary",
        Employer.is_deleted == False,
    ).order_by(Employer.name).all()
    return [{"classification_code": code, "name": name} for code, name in rows]
