import pandas as pd
from decimal import Decimal
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models.contract import Contract
from models.deposits import AnnualMandate, DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.transfer import CreditTransfer

def calculate_real_balance(db: Session, employer_code: str, funding_year: int) -> float:
    """
    Calculates the real financial balance for a specific employer and funding year.

    Formula: (Total Deposits + Transfers In) - (Total Payments + Transfers Out)
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

    # 3. Calculate Transfers Out (funds sent from this employer or its subsidiaries)
    transfers_out_query = db.query(func.sum(CreditTransfer.amount)).join(
        Employer, CreditTransfer.source_employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code
        ),
        CreditTransfer.fiscal_year == funding_year,
        CreditTransfer.is_deleted == False,
        Employer.is_deleted == False
    ).scalar()
    
    transfers_out = transfers_out_query or Decimal('0.0')

    # 4. Calculate Transfers In (funds received by this employer)
    transfers_in_query = db.query(func.sum(CreditTransfer.amount)).filter(
        CreditTransfer.destination_employer_code == employer_code,
        CreditTransfer.fiscal_year == funding_year,
        CreditTransfer.is_deleted == False
    ).scalar()
    
    transfers_in = transfers_in_query or Decimal('0.0')

    # 5. Calculate Real Balance
    real_balance = total_deposits + transfers_in - transfers_out - total_payments
    
    return float(real_balance)

def get_mandated_amount(db: Session, employer_code: str, fiscal_year: int) -> float:
    """
    Retrieves the mandated budget amount (اعتبار تکلیفی) for a specific employer.
    """
    mandate = db.query(AnnualMandate).filter(
        AnnualMandate.employer_code == employer_code,
        AnnualMandate.fiscal_year == fiscal_year,
        AnnualMandate.is_deleted == False
    ).first()
    
    return float(mandate.mandated_amount) if mandate else 0.0


def _codes_to_include(db: Session, employer: Employer) -> list[str]:
    """Return employer code plus subsidiary codes for Mother entities."""
    if employer.employer_type == "Mother":
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer.classification_code,
            Employer.is_deleted == False,
        ).all()
        return [employer.classification_code] + [s[0] for s in subsidiaries]
    return [employer.classification_code]


def get_all_employers_financials(db: Session) -> pd.DataFrame:
    """
    Aggregate financial data for all active employers across all fiscal years.

    For Mother employers, deposits, mandates, payments, and transfers are rolled up
    to include all subsidiaries. Balance formula (single source of truth):

        (Total Deposits + Transfers In) - (Total Payments + Transfers Out)
    """
    employers = db.query(Employer).filter(
        Employer.status == "Active",
        Employer.is_deleted == False,
    ).all()

    all_data = []

    for employer in employers:
        employer_code = employer.classification_code
        employer_name = employer.name
        codes_to_include = _codes_to_include(db, employer)

        mandates_query = db.query(
            AnnualMandate.fiscal_year.label("year"),
            func.sum(AnnualMandate.mandated_amount).label("mandated_amount"),
        ).filter(
            AnnualMandate.employer_code.in_(codes_to_include),
            AnnualMandate.is_deleted == False,
        ).group_by(AnnualMandate.fiscal_year)

        deposits_query = db.query(
            DepositReceipt.fiscal_year.label("year"),
            func.sum(DepositReceipt.deposit_amount).label("deposit_amount"),
        ).filter(
            DepositReceipt.employer_code.in_(codes_to_include),
            DepositReceipt.is_deleted == False,
        ).group_by(DepositReceipt.fiscal_year)

        payments_query = db.query(
            Payment.funding_year.label("year"),
            func.sum(Payment.amount).label("payment_amount"),
        ).join(
            Contract, Payment.contract_tracking_code == Contract.tracking_code
        ).filter(
            Contract.employer_code.in_(codes_to_include),
            Payment.is_deleted == False,
            Contract.is_deleted == False,
        ).group_by(Payment.funding_year)

        transfers_in_query = db.query(
            CreditTransfer.fiscal_year.label("year"),
            func.sum(CreditTransfer.amount).label("transfer_in"),
        ).filter(
            CreditTransfer.destination_employer_code.in_(codes_to_include),
            CreditTransfer.is_deleted == False,
        ).group_by(CreditTransfer.fiscal_year)

        transfers_out_query = db.query(
            CreditTransfer.fiscal_year.label("year"),
            func.sum(CreditTransfer.amount).label("transfer_out"),
        ).filter(
            CreditTransfer.source_employer_code.in_(codes_to_include),
            CreditTransfer.is_deleted == False,
        ).group_by(CreditTransfer.fiscal_year)

        metric_frames = []
        for query, columns in (
            (mandates_query, ["year", "mandated_amount"]),
            (deposits_query, ["year", "deposit_amount"]),
            (payments_query, ["year", "payment_amount"]),
            (transfers_in_query, ["year", "transfer_in"]),
            (transfers_out_query, ["year", "transfer_out"]),
        ):
            df_metric = pd.read_sql(query.statement, db.bind)
            df_metric = df_metric.reindex(columns=columns).fillna(0.0)
            metric_frames.append(df_metric)

        df_merged = metric_frames[0]
        for df_metric in metric_frames[1:]:
            df_merged = df_merged.merge(df_metric, on="year", how="outer")

        df_merged = df_merged.fillna(0).infer_objects(copy=False)
        df_merged["employer_code"] = employer_code
        df_merged["employer_name"] = employer_name

        required_cols = [
            "mandated_amount",
            "deposit_amount",
            "payment_amount",
            "transfer_in",
            "transfer_out",
        ]
        for col in required_cols:
            if col not in df_merged.columns:
                df_merged[col] = 0.0

        df_merged["balance"] = (
            df_merged["deposit_amount"] + df_merged["transfer_in"]
        ) - (
            df_merged["payment_amount"] + df_merged["transfer_out"]
        )

        all_data.append(df_merged)

    if not all_data:
        return pd.DataFrame()

    df_all = pd.concat(all_data, ignore_index=True)
    return df_all[
        [
            "employer_code",
            "employer_name",
            "year",
            "mandated_amount",
            "deposit_amount",
            "payment_amount",
            "transfer_in",
            "transfer_out",
            "balance",
        ]
    ]


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
