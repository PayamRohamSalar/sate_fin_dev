from decimal import Decimal
from typing import Sequence

import pandas as pd
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from models.contract import Contract
from models.deposits import AnnualMandate, DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.transfer import CreditTransfer


def lock_active_contracts(
    db: Session,
    contract_codes: Sequence[str],
) -> dict[str, Contract]:
    """
    Lock and return active contracts in deterministic tracking-code order.

    PostgreSQL keeps the row-level locks until the surrounding transaction
    commits or rolls back. Sorting the unique keys gives concurrent payment
    transactions a consistent lock order and reduces deadlock risk.

    Args:
        db: Active SQLAlchemy session with an open transaction.
        contract_codes: Contract tracking codes that participate in the
            financial operation.

    Returns:
        A mapping from tracking code to the locked active contract.
    """
    unique_codes = sorted(set(contract_codes))
    if not unique_codes:
        return {}

    contracts = (
        db.query(Contract)
        .filter(
            Contract.tracking_code.in_(unique_codes),
            Contract.is_deleted == False,
        )
        .order_by(Contract.tracking_code)
        .with_for_update()
        .all()
    )
    return {contract.tracking_code: contract for contract in contracts}


def lock_active_employers(
    db: Session,
    employer_codes: Sequence[str],
) -> dict[str, Employer]:
    """
    Lock and return active employers in deterministic classification-code order.

    The employer row is the serialization point for balance-changing operations.
    Callers must retain the same transaction while calculating balances and
    inserting payments so concurrent requests cannot validate stale balances.

    Args:
        db: Active SQLAlchemy session with an open transaction.
        employer_codes: Employer classification codes to serialize.

    Returns:
        A mapping from classification code to the locked active employer.
    """
    unique_codes = sorted(set(employer_codes))
    if not unique_codes:
        return {}

    employers = (
        db.query(Employer)
        .filter(
            Employer.classification_code.in_(unique_codes),
            Employer.is_deleted == False,
        )
        .order_by(Employer.classification_code)
        .with_for_update()
        .all()
    )
    return {employer.classification_code: employer for employer in employers}


def lock_active_contract_and_employer(
    db: Session,
    contract_code: str,
) -> tuple[Contract, Employer]:
    """
    Lock one active contract and its active employer for financial processing.

    Args:
        db: Active SQLAlchemy session with an open transaction.
        contract_code: Tracking code of the contract to lock.

    Returns:
        The locked contract and its locked employer.

    Raises:
        ValueError: If the contract or linked employer is missing or soft-deleted.
    """
    contract = lock_active_contracts(db, [contract_code]).get(contract_code)
    if contract is None:
        raise ValueError(
            f"Contract with tracking code '{contract_code}' not found or has been deleted."
        )

    employer = lock_active_employers(db, [contract.employer_code]).get(
        contract.employer_code
    )
    if employer is None:
        raise ValueError(
            f"Employer with classification code '{contract.employer_code}' "
            "not found or has been deleted."
        )

    return contract, employer


def get_contracts_with_dynamic_status(
    db: Session,
    threshold_year: int = 1402,
):
    """
    Retrieve contracts with a lifecycle status calculated entirely in SQL.

    Non-deleted payments are aggregated per non-deleted contract. A contract is
    completed when its total payments cover its total amount. Otherwise, its
    most recent activity year is the greater of the last payment funding year
    and the approximated Jalali contract creation year. Activity before
    ``threshold_year`` is classified as stagnant; all other activity is active.
    The persisted ``Contract.status`` column is never modified.

    Args:
        db: Active SQLAlchemy database session.
        threshold_year: Jalali year used as the active/stagnant boundary.

    Returns:
        SQLAlchemy result rows containing the contract entity, aggregated
        payment values, Jalali activity years, and the dynamic status.
    """
    total_paid = func.coalesce(func.sum(Payment.amount), 0)
    last_payment_funding_year = func.max(Payment.funding_year)
    gregorian_contract_year = func.extract("year", Contract.contract_date)
    contract_creation_year = case(
        (
            func.to_char(Contract.contract_date, "MMDD") < "0321",
            gregorian_contract_year - 622,
        ),
        else_=gregorian_contract_year - 621,
    )
    activity_year = func.greatest(
        func.coalesce(last_payment_funding_year, contract_creation_year, 0),
        func.coalesce(contract_creation_year, last_payment_funding_year, 0),
    )
    dynamic_status = case(
        (total_paid >= Contract.total_amount, "Completed"),
        (activity_year < threshold_year, "Stagnant"),
        else_="Active",
    )

    statement = (
        select(
            Contract,
            total_paid.label("total_paid"),
            func.coalesce(last_payment_funding_year, 0).label(
                "last_payment_funding_year"
            ),
            contract_creation_year.label("contract_creation_year"),
            activity_year.label("activity_year"),
            dynamic_status.label("dynamic_status"),
        )
        .outerjoin(
            Payment,
            and_(
                Payment.contract_tracking_code == Contract.tracking_code,
                Payment.is_deleted == False,
            ),
        )
        .where(Contract.is_deleted == False)
        .group_by(Contract.tracking_code)
    )

    return db.execute(statement).all()


def calculate_real_balance(
    db: Session,
    employer_code: str,
    funding_year: int,
    *,
    lock_employer: bool = False,
) -> float:
    """
    Calculate the real balance for an active employer and funding year.

    Formula: ``(Deposits + Transfers In) - (Payments + Transfers Out)``.

    Args:
        db: Active SQLAlchemy database session.
        employer_code: Employer classification code.
        funding_year: Funding year used by all balance components.
        lock_employer: When true, acquire a PostgreSQL ``FOR UPDATE`` lock on
            the active employer row before reading financial aggregates. The
            caller must keep the transaction open through the related write.

    Returns:
        The calculated balance in base Rials.

    Raises:
        ValueError: If ``lock_employer`` is true and the employer is missing or
            soft-deleted.
    """
    if lock_employer and employer_code not in lock_active_employers(
        db, [employer_code]
    ):
        raise ValueError(
            f"Employer with classification code '{employer_code}' "
            "not found or has been deleted."
        )

    deposits_query = db.query(func.sum(DepositReceipt.deposit_amount)).join(
        Employer, DepositReceipt.employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code,
        ),
        DepositReceipt.fiscal_year == funding_year,
        DepositReceipt.is_deleted == False,
        Employer.is_deleted == False,
    ).scalar()
    total_deposits = deposits_query or Decimal("0.0")

    payments_query = db.query(func.sum(Payment.amount)).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code == employer_code,
        Payment.funding_year == funding_year,
        Payment.is_deleted == False,
        Contract.is_deleted == False,
    ).scalar()
    total_payments = payments_query or Decimal("0.0")

    transfers_out_query = db.query(func.sum(CreditTransfer.amount)).join(
        Employer, CreditTransfer.source_employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code,
        ),
        CreditTransfer.fiscal_year == funding_year,
        CreditTransfer.is_deleted == False,
        Employer.is_deleted == False,
    ).scalar()
    transfers_out = transfers_out_query or Decimal("0.0")

    transfers_in_query = db.query(func.sum(CreditTransfer.amount)).filter(
        CreditTransfer.destination_employer_code == employer_code,
        CreditTransfer.fiscal_year == funding_year,
        CreditTransfer.is_deleted == False,
    ).scalar()
    transfers_in = transfers_in_query or Decimal("0.0")

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


def validate_payment_impact(
    db: Session,
    contract_code: str,
    payment_amount: float,
    funding_year: int,
    *,
    lock_rows: bool = False,
) -> dict:
    """
    Validate a payment's impact on the linked employer's real balance.

    This function implements FR-18, FR-19, and FR-20. A negative projected
    balance is reported through ``is_negative`` and never raises an error.

    Args:
        db: Active SQLAlchemy database session.
        contract_code: Contract tracking code linked to the payment.
        payment_amount: Payment amount in base Rials.
        funding_year: Funding year for the payment.
        lock_rows: When true, lock the active contract and employer rows for
            the duration of the caller's transaction.

    Returns:
        A dictionary containing employer code, current balance, payment amount,
        projected balance, and whether the projected balance is negative.

    Raises:
        ValueError: If the contract or linked employer is missing or soft-deleted.
    """
    if lock_rows:
        contract, _ = lock_active_contract_and_employer(db, contract_code)
    else:
        contract = (
            db.query(Contract)
            .join(
                Employer,
                and_(
                    Contract.employer_code == Employer.classification_code,
                    Employer.is_deleted == False,
                ),
            )
            .filter(
                Contract.tracking_code == contract_code,
                Contract.is_deleted == False,
            )
            .first()
        )

    if contract is None:
        raise ValueError(
            f"Contract with tracking code '{contract_code}' not found or has been deleted."
        )

    employer_code = contract.employer_code
    current_balance = calculate_real_balance(db, employer_code, funding_year)
    new_balance = current_balance - payment_amount

    return {
        "employer_code": employer_code,
        "current_balance": current_balance,
        "payment_amount": payment_amount,
        "new_balance": new_balance,
        "is_negative": new_balance < 0,
    }
