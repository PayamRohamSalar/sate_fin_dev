from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from decimal import Decimal

# Import models from the root-level 'models' directory
from models.employer import Employer
from models.deposits import DepositReceipt
from models.contract import Contract
from models.payment import Payment

def calculate_real_balance(db: Session, employer_code: str, funding_year: int) -> float:
    """
    Calculates the real financial balance for a specific employer and funding year.
    Formula: Sum of deposits (self + subsidiaries) - Sum of payments linked to employer's contracts for the specified funding_year.
    """
    
    # 1. Calculate Total Deposits (Including subsidiaries)
    # Finding the employer and all its subsidiaries using the parent_code constraint
    deposits_query = db.query(func.sum(DepositReceipt.deposit_amount)).join(
        Employer, DepositReceipt.employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code
        ),
        DepositReceipt.fiscal_year == funding_year,
        DepositReceipt.is_deleted == False,
        Employer.is_deleted == False
    ).scalar()
    
    total_deposits = deposits_query or Decimal('0.0')

    # 2. Calculate Total Payments based on funding_year (NOT payment_year)
    payments_query = db.query(func.sum(Payment.amount)).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code == employer_code,
        Payment.funding_year == funding_year,
        Payment.is_deleted == False,
        Contract.is_deleted == False
    ).scalar()

    total_payments = payments_query or Decimal('0.0')

    # 3. Calculate Real Balance
    real_balance = total_deposits - total_payments
    
    return float(real_balance)

def get_mandated_amount(db: Session, employer_code: str, fiscal_year: int) -> float:
    """
    Retrieves the mandated budget amount (اعتبار تکلیفی) for a specific employer.
    """
    from models.deposits import AnnualMandate
    
    mandate = db.query(AnnualMandate).filter(
        AnnualMandate.employer_code == employer_code,
        AnnualMandate.fiscal_year == fiscal_year,
        AnnualMandate.is_deleted == False
    ).first()
    
    return float(mandate.mandated_amount) if mandate else 0.0
def validate_payment_impact(db: Session, contract_code: str, payment_amount: float, funding_year: int) -> dict:
    """
    Validates the impact of a payment on the employer's balance.
    
    This function implements FR-18, FR-19, FR-20 from the conceptual design:
    - FR-18: Query the contract to find the linked employer
    - FR-19: Calculate current balance and project new balance after payment
    - FR-20: Warn (but do not block) if the balance becomes negative
    
    Args:
        db: Database session
        contract_code: The contract tracking code
        payment_amount: The amount to be paid
        funding_year: The funding year for the payment
    
    Returns:
        dict containing:
            - employer_code: The employer's classification code
            - current_balance: Current balance before payment
            - payment_amount: The payment amount
            - new_balance: Projected balance after payment
            - is_negative: Whether the new balance will be negative
    
    Raises:
        ValueError: If contract is not found or has been deleted
    """
    
    # Step 1: Find the contract and get the employer_code
    contract = db.query(Contract).filter(
        Contract.tracking_code == contract_code,
        Contract.is_deleted == False
    ).first()
    
    if not contract:
        raise ValueError(f"Contract with tracking code '{contract_code}' not found or has been deleted.")
    
    employer_code = contract.employer_code
    
    # Step 2: Calculate current balance using existing function
    current_balance = calculate_real_balance(db, employer_code, funding_year)
    
    # Step 3: Calculate new balance after payment
    new_balance = current_balance - payment_amount
    
    # Step 4: Determine if balance becomes negative
    is_negative = new_balance < 0
    
    # Step 5: Return validation result
    return {
        "employer_code": employer_code,
        "current_balance": current_balance,
        "payment_amount": payment_amount,
        "new_balance": new_balance,
        "is_negative": is_negative
    }
