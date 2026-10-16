from datetime import date
from decimal import Decimal
from typing import Sequence

import pandas as pd
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from core.date_helper import to_jalali_date
from models.contract import Contract
from models.deposits import AnnualMandate, DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.researchers import Researcher
from models.transfer import CreditTransfer
from models.trustee_payments import TrusteePayment
from models.university import University


class InsufficientFundsError(ValueError):
    """Raised when a payment would exceed the employer's real balance.

    A ``ValueError`` subclass so existing ``except ValueError`` call sites
    still catch it, while callers that need to distinguish "insufficient
    funds" from other validation failures (e.g. "contract not found") can
    match on this specific type instead of parsing the error message.

    Attributes
    ----------
    employer_code : str
        The employer whose balance was insufficient.
    funding_year : int
        The funding year the balance was checked against.
    current_balance : float
        The employer's real balance before this payment.
    amount : float
        The payment amount that was rejected.
    deficit : float
        ``amount - current_balance`` — how much the payment exceeds the
        available balance, in Rials.
    """

    def __init__(
        self,
        employer_code: str,
        funding_year: int,
        current_balance: float,
        amount: float,
    ) -> None:
        self.employer_code = employer_code
        self.funding_year = funding_year
        self.current_balance = current_balance
        self.amount = amount
        self.deficit = amount - current_balance
        super().__init__(
            "موجودی کافی نیست: "
            f"مانده فعلی کارفرما '{employer_code}' برای سال مالی "
            f"{funding_year} برابر {current_balance:,.0f} ریال است، اما "
            f"مبلغ درخواستی {amount:,.0f} ریال می‌باشد "
            f"(کسری: {self.deficit:,.0f} ریال)."
        )


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
    "Payments" includes both ``Final`` and ``Draft`` status rows: a draft
    reserves funds against the employer's balance the moment it is staged
    in the batch-payment cart, so a second draft cannot be added against
    money a first, not-yet-finalized draft has already claimed.

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
        Payment.status.in_(("Final", "Draft")),
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


# Fiscal years whose leftover credit can be moved by a credit transfer
# (انتقال اعتبار) -- see ``calculate_combined_pool_balance`` below.
#
# Revised 2026-10-16 at Payam's direction: by law a transfer can only come
# from PRIOR years' unspent credit, so the current year (1405) is never part
# of the transferable pool. 1405 credit is its own balance
# (:func:`calculate_balance_1405`) and can only be spent in 1405. Which pool
# a payment draws on is a free choice recorded in ``Payment.funding_year``
# (not the calendar year the payment is made in): a 1405 payment may well be
# funded from 1404 money, and a company may pay from 1405 while still holding
# a 1404 balance. Balances before 1402 are out of scope (the Fund did not
# exist).
TRANSFER_POOL_YEARS = (1402, 1404)

# The current fiscal year: its own balance, never transferable.
CURRENT_YEAR_POOL = 1405

# Every fiscal year in the Fund's ledger. The Fund's own report does not
# separate 1405 from the earlier pools (it folds 1405 deposits and spending
# into the 1404 pool -- see scripts/reconcile_atf_audit.py), so the
# Secretariat-vs-Fund comparison (``get_combined_pool_breakdown``,
# services/fund_report.py) keeps working over this whole range.
ALL_FUND_YEARS = (1402, 1404, 1405)


def calculate_gross_pool_balance(db: Session, employer_code: str) -> float:
    """
    Combined 1402+1404 balance **before any credit transfer is
    netted in** -- deposits minus expense only.

    Added 2026-10-12 for the موسسه تحقیقات سیاست علمی کشور (128342) funding
    report: that institute acts purely as a broker/کارگزار with no mandate
    of its own, so every one of its contracts is funded entirely by credit
    transfers (اصلاحیه تبصره ۲) out of OTHER employers' spare balance. To
    show "how much headroom did employer X have before this transfer, and
    what's left after", you need both this gross figure and
    :func:`calculate_combined_pool_balance` (the net-of-transfers figure)
    side by side -- this function is the "before" half.

    Same Mother/Subsidiary roll-up and :data:`TRANSFER_POOL_YEARS` scope as
    :func:`calculate_combined_pool_balance`; the only difference is the
    transfer terms are left out.
    """
    years = list(TRANSFER_POOL_YEARS)

    total_deposits = db.query(func.sum(DepositReceipt.deposit_amount)).join(
        Employer, DepositReceipt.employer_code == Employer.classification_code
    ).filter(
        or_(Employer.classification_code == employer_code, Employer.parent_code == employer_code),
        DepositReceipt.fiscal_year.in_(years),
        DepositReceipt.is_deleted == False, Employer.is_deleted == False,  # noqa: E712
    ).scalar() or Decimal("0.0")

    total_payments = db.query(func.sum(Payment.amount)).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code == employer_code,
        Payment.funding_year.in_(years),
        Payment.is_deleted == False, Payment.status.in_(("Final", "Draft")),
        Contract.is_deleted == False,  # noqa: E712
    ).scalar() or Decimal("0.0")

    return float(total_deposits - total_payments)


def calculate_combined_pool_balance(
    db: Session,
    employer_code: str,
    *,
    lock_employer: bool = False,
) -> float:
    """
    Balance available to an employer for a credit transfer (انتقال اعتبار),
    and the authoritative "current position" figure used wherever a single
    across-years balance is needed (e.g. the commitment/free-balance report).

    Added 2026-09-16 at Payam's request, after a real incident: our 1402
    deposit figure for an employer was overstated (a data error, since
    corrected -- see ``scripts/fix_deposits_1402.py``), which meant a real,
    legitimate transfer recorded against ``fiscal_year=1402`` alone looked
    like it exceeded that single year's balance once the deposit was fixed,
    even though the employer's TRUE combined position covered it easily.
    Rather than keep re-hitting this whenever one year's figures are
    revised, transfers are now checked against the **combined** balance
    across :data:`TRANSFER_POOL_YEARS` instead of a single year. This does
    not change ``calculate_real_balance`` itself, which other views
    (per-year balance sheets, payment validation) still use as single-year.

    Revised 2026-10-16: the pool is 1402+1404 only. 1405 credit is not
    transferable (a transfer must come from prior years' leftover), so
    1405 deposits and 1405-funded payments are deliberately left out here
    and reported separately by :func:`calculate_balance_1405`. (Between
    2026-10-04 and 2026-10-16 the pool also folded 1405 in, after a bug fix
    that stopped ``calculate_real_balance``-per-year sums from silently
    dropping 1405 activity; that was the wrong fix for the rule above.)
    Each component is queried across all of :data:`TRANSFER_POOL_YEARS` at
    once, with the same Mother/Subsidiary roll-up as
    ``calculate_real_balance``.

    Args:
        db: Active SQLAlchemy database session.
        employer_code: Employer classification code (the transfer's source).
        lock_employer: When true, acquire a ``FOR UPDATE`` lock on the
            active employer row first; the caller must keep the transaction
            open through the related write (same contract as
            ``calculate_real_balance``).

    Returns:
        The combined balance across :data:`TRANSFER_POOL_YEARS`, in base Rials.

    Raises:
        ValueError: If ``lock_employer`` is true and the employer is missing
            or soft-deleted.
    """
    if lock_employer and employer_code not in lock_active_employers(db, [employer_code]):
        raise ValueError(
            f"Employer with classification code '{employer_code}' not found or has been deleted."
        )

    years = list(TRANSFER_POOL_YEARS)

    total_deposits = db.query(func.sum(DepositReceipt.deposit_amount)).join(
        Employer, DepositReceipt.employer_code == Employer.classification_code
    ).filter(
        or_(Employer.classification_code == employer_code, Employer.parent_code == employer_code),
        DepositReceipt.fiscal_year.in_(years),
        DepositReceipt.is_deleted == False, Employer.is_deleted == False,  # noqa: E712
    ).scalar() or Decimal("0.0")

    total_payments = db.query(func.sum(Payment.amount)).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code == employer_code,
        Payment.funding_year.in_(years),
        Payment.is_deleted == False, Payment.status.in_(("Final", "Draft")),
        Contract.is_deleted == False,  # noqa: E712
    ).scalar() or Decimal("0.0")

    transfers_out = db.query(func.sum(CreditTransfer.amount)).join(
        Employer, CreditTransfer.source_employer_code == Employer.classification_code
    ).filter(
        or_(Employer.classification_code == employer_code, Employer.parent_code == employer_code),
        CreditTransfer.fiscal_year.in_(years),
        CreditTransfer.is_deleted == False, Employer.is_deleted == False,  # noqa: E712
    ).scalar() or Decimal("0.0")

    transfers_in = db.query(func.sum(CreditTransfer.amount)).filter(
        CreditTransfer.destination_employer_code == employer_code,
        CreditTransfer.fiscal_year.in_(years),
        CreditTransfer.is_deleted == False,  # noqa: E712
    ).scalar() or Decimal("0.0")

    return float(total_deposits + transfers_in - transfers_out - total_payments)


def calculate_balance_1405(db: Session, employer_code: str) -> float:
    """
    Current-year (1405) balance: 1405 deposits minus payments funded from
    1405 (``Payment.funding_year == 1405``). Not transferable, and credit
    transfers never touch it (transfers can only be tagged 1402/1404).

    Thin wrapper over :func:`calculate_real_balance` so the Mother/Subsidiary
    roll-up and Draft/Final handling stay defined in one place.
    """
    return calculate_real_balance(db, employer_code, CURRENT_YEAR_POOL)


def get_holding_group_financials(
    db: Session,
    holding_company_code: str,
    *,
    since_jalali_year: int = 1402,
    include_group_total: bool = True,
) -> pd.DataFrame:
    """
    Per-(member, year) financial detail for a reporting-only holding group.

    Added 2026-09-27 at Payam's request: some employers (e.g. هر یک از ۳۱
    شرکت آب منطقه‌ای استانی) are fully financially independent -- they hold
    their own contracts and have their own deposit/expense/balance -- but
    are organizationally grouped under a holding company (e.g. شرکت
    مادرتخصصی مدیریت منابع آب ایران) that wants to see all of them side by
    side. This is deliberately **not** the existing Mother/Subsidiary
    roll-up (``parent_code`` + ``calculate_real_balance``'s merging of
    Subsidiary employers into their Mother for balance purposes): every
    member here keeps its own numbers, nothing is merged or netted across
    employers. See ``Employer.holding_company_code``'s docstring for the
    full rationale.

    Members are every employer with ``holding_company_code ==
    holding_company_code``, plus the holding company itself (Payam's
    explicit requirement: "وقتی مدیریت منابع آب گزارش زیرمجموعه‌هایش را
    می‌خواهد، وضعیت خودش را نیز در گزارش به او می‌دهیم").

    Args:
        db: Active SQLAlchemy database session.
        holding_company_code: The holding company's classification_code.
        since_jalali_year: Inclusive lower bound (Jalali year) on every
            metric -- contracts by ``Contract.contract_date``'s Jalali
            year, mandate/deposit/expense by their own ``fiscal_year``/
            ``funding_year`` (default 1402).
        include_group_total: When true (default), append one synthetic
            "جمع گروه" row per year summing every member (Payam confirmed
            he wants both the detail and this total).

    Returns:
        One row per (employer_code, year) [plus one "جمع گروه" row per
        year if requested], columns: ``employer_code``, ``employer_name``,
        ``is_holding_company``, ``year``, ``contracts_count``,
        ``contracts_amount``, ``mandated_amount``, ``deposit_amount``,
        ``expense_amount``. Sorted by year, then holding company first,
        then member name.
    """
    members = (
        db.query(Employer)
        .filter(
            or_(
                Employer.classification_code == holding_company_code,
                Employer.holding_company_code == holding_company_code,
            ),
            Employer.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    member_codes = [m.classification_code for m in members]
    member_names = {m.classification_code: m.name for m in members}
    return _group_member_financials(
        db, member_codes, member_names, since_jalali_year=since_jalali_year,
        include_group_total=include_group_total, highlight_code=holding_company_code,
    )


def get_ministry_group_financials(
    db: Session,
    upper_organization: str,
    *,
    since_jalali_year: int = 1402,
    include_group_total: bool = True,
) -> pd.DataFrame:
    """
    Per-(employer, year) financial detail for every employer under one
    executive body/ministry (``Employer.upper_organization``), for the
    "عملکرد دستگاهی" view (e.g. "شرکت‌های تابعه وزارت نیرو").

    Unlike :func:`get_holding_group_financials`, no new column is needed
    here -- ``upper_organization`` already exists and is populated on every
    employer, so this simply groups by it. Per Payam's explicit choice
    (2026-09-27): Mother AND Subsidiary employers under this ministry are
    both listed as their own rows (a Subsidiary's real, standalone
    deposit/contract activity is visible here even though it's rolled into
    its Mother's balance everywhere else in the system) -- this view is
    purely descriptive, not a balance calculation, so no double-counting
    concern applies.

    Args:
        db: Active SQLAlchemy database session.
        upper_organization: Exact ``Employer.upper_organization`` value to
            filter on (e.g. "وزارت نیرو").
        since_jalali_year: Same semantics as
            :func:`get_holding_group_financials`.
        include_group_total: Same semantics as
            :func:`get_holding_group_financials`.

    Returns:
        Same shape as :func:`get_holding_group_financials`, with
        ``is_holding_company`` always ``False`` (no single employer is
        singled out for a ministry-wide view).
    """
    members = (
        db.query(Employer)
        .filter(Employer.upper_organization == upper_organization, Employer.is_deleted == False)  # noqa: E712
        .all()
    )
    member_codes = [m.classification_code for m in members]
    member_names = {m.classification_code: m.name for m in members}
    return _group_member_financials(
        db, member_codes, member_names, since_jalali_year=since_jalali_year,
        include_group_total=include_group_total, highlight_code=None,
    )


def _group_member_financials(
    db: Session,
    member_codes: list[str],
    member_names: dict[str, str],
    *,
    since_jalali_year: int,
    include_group_total: bool,
    highlight_code: str | None,
) -> pd.DataFrame:
    """Shared per-(employer, year) aggregation behind
    :func:`get_holding_group_financials` and
    :func:`get_ministry_group_financials` -- see those for the business
    context. Every member keeps its own numbers; nothing is merged or
    netted across employers (deliberately not the Mother/Subsidiary
    financial roll-up)."""
    contract_rows = (
        db.query(Contract.employer_code, Contract.contract_date, Contract.total_amount)
        .filter(Contract.employer_code.in_(member_codes), Contract.is_deleted == False)  # noqa: E712
        .all()
    )
    mandate_rows = (
        db.query(AnnualMandate.employer_code, AnnualMandate.fiscal_year, AnnualMandate.mandated_amount)
        .filter(AnnualMandate.employer_code.in_(member_codes), AnnualMandate.is_deleted == False)  # noqa: E712
        .all()
    )
    deposit_rows = (
        db.query(DepositReceipt.employer_code, DepositReceipt.fiscal_year, DepositReceipt.deposit_amount)
        .filter(DepositReceipt.employer_code.in_(member_codes), DepositReceipt.is_deleted == False)  # noqa: E712
        .all()
    )
    expense_rows = (
        db.query(Contract.employer_code, Payment.funding_year, Payment.amount)
        .join(Payment, Payment.contract_tracking_code == Contract.tracking_code)
        .filter(
            Contract.employer_code.in_(member_codes),
            Payment.is_deleted == False, Contract.is_deleted == False,  # noqa: E712
        )
        .all()
    )

    cell: dict[tuple[str, int], dict] = {}

    def bucket(code: str, year: int) -> dict:
        return cell.setdefault(
            (code, year),
            {"contracts_count": 0, "contracts_amount": 0.0, "mandated_amount": 0.0,
             "deposit_amount": 0.0, "expense_amount": 0.0},
        )

    for code, contract_date, total_amount in contract_rows:
        if contract_date is None:
            continue
        year = to_jalali_date(contract_date).year
        if year < since_jalali_year:
            continue
        b = bucket(code, year)
        b["contracts_count"] += 1
        b["contracts_amount"] += float(total_amount or 0)

    for code, year, amount in mandate_rows:
        if year < since_jalali_year:
            continue
        bucket(code, year)["mandated_amount"] += float(amount or 0)

    for code, year, amount in deposit_rows:
        if year < since_jalali_year:
            continue
        bucket(code, year)["deposit_amount"] += float(amount or 0)

    for code, year, amount in expense_rows:
        if year is None or year < since_jalali_year:
            continue
        bucket(code, year)["expense_amount"] += float(amount or 0)

    years = sorted({year for (_, year) in cell})
    records = []
    for year in years:
        for code in member_codes:
            b = cell.get((code, year))
            if b is None:
                continue
            records.append({
                "employer_code": code,
                "employer_name": member_names[code],
                "is_holding_company": code == highlight_code,
                "year": year,
                **b,
            })
        if include_group_total:
            total = {"contracts_count": 0, "contracts_amount": 0.0, "mandated_amount": 0.0,
                     "deposit_amount": 0.0, "expense_amount": 0.0}
            for code in member_codes:
                b = cell.get((code, year))
                if b is None:
                    continue
                for k in total:
                    total[k] += b[k]
            records.append({
                "employer_code": None,
                "employer_name": "جمع گروه",
                "is_holding_company": False,
                "year": year,
                **total,
            })

    columns = [
        "employer_code", "employer_name", "is_holding_company", "year",
        "contracts_count", "contracts_amount", "mandated_amount", "deposit_amount", "expense_amount",
    ]
    return pd.DataFrame.from_records(records, columns=columns)


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

    Supersedes the original FR-18/FR-19/FR-20 "warn but allow" behavior:
    negative balances are now a **hard block**, not a warning. A projected
    balance below zero raises :class:`InsufficientFundsError` instead of
    being reported through an ``is_negative`` flag — there is no longer a
    success return path for an unaffordable payment.

    Args:
        db: Active SQLAlchemy database session.
        contract_code: Contract tracking code linked to the payment.
        payment_amount: Payment amount in base Rials.
        funding_year: Funding year for the payment.
        lock_rows: When true, lock the active contract and employer rows for
            the duration of the caller's transaction.

    Returns:
        A dictionary containing employer code, current balance, payment
        amount, and projected balance — always affordable, since an
        unaffordable payment raises instead of returning.

    Raises:
        ValueError: If the contract or linked employer is missing or
            soft-deleted.
        InsufficientFundsError: If ``current_balance - payment_amount`` is
            negative.
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

    if new_balance < 0:
        raise InsufficientFundsError(
            employer_code, funding_year, current_balance, payment_amount
        )

    return {
        "employer_code": employer_code,
        "current_balance": current_balance,
        "payment_amount": payment_amount,
        "new_balance": new_balance,
        "is_negative": False,
    }


STAGNANT_CONTRACT_STATUSES = ("خاتمه‌یافته", "آغاز نشده", "راکد", "فعال")


def get_contract_status_overview(
    db: Session,
    *,
    since_jalali_year: int = 1402,
    dormant_days_threshold: int = 365,
    as_of: date | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Build a per-contract activity/status overview for the "قراردادهای
    رسوب‌کرده" (stagnant contracts) dashboard, scoped to contracts concluded
    from ``since_jalali_year`` onward.

    This is deliberately a different question from
    ``get_contracts_with_dynamic_status`` above: that function buckets a
    contract's *entire* history into Active/Stagnant/Completed by comparing
    the fiscal ``funding_year`` of its last payment against a fixed cliff
    year. This function instead scopes to contracts *created* from
    ``since_jalali_year`` onward (by ``Contract.contract_date``, Jalali
    year) and measures dormancy in real elapsed calendar days against a
    rolling ``as_of`` reference (default: today) — a live,
    continuously-shifting measure rather than a static year cliff. Both are
    legitimate, separate views; do not merge or replace one with the other.
    See Docs/SATE_Living_Documentation.md §4.1 on why ``funding_year``
    (budget year) and ``payment_date``/``payment_year`` (cash-flow date)
    must not be conflated.

    The "last payment" date is ``COALESCE(Payment.payment_date,
    Payment.notification_date)`` — prefer the real cash-disbursement date
    when known, but fall back to the notification/ابلاغ date (the date the
    payment was officially communicated) when it isn't. This is not a
    cosmetic choice: as of 2026-08-11, every row in ``payments`` has a
    ``NULL`` ``payment_date`` (the column has never actually been populated
    in this database, despite the fallback rule in
    ``scripts/import_payments_upsert.py``'s docstring describing it as a
    per-row fallback), while ``notification_date`` is now 100% populated
    after the ``Q_PaymentsFrom1402.xlsx`` reconciliation
    (``scripts/reconcile_q_payments_from_1402.py`` +
    ``scripts/backfill_notification_date_placeholder.py``). Before this fix,
    ``last_payment_date`` was unconditionally ``NULL`` for every contract,
    so *every* contract with payment history that wasn't yet "خاتمه‌یافته"
    was conservatively misclassified as "راکد" via the
    ``missing_payment_date_flags`` path below — that is the exact "۲۹۹
    قرارداد ... تاریخ پرداخت ... نامعتبر/خالی" symptom the notification-date
    backfill alone could not fix, since this query never read
    ``notification_date`` at all until now.

    ``trustee_payments`` (پرداخت‌های امانی — payments the executing
    institution funded directly from its own resources, outside the
    employer-managed budget pool; see ``models/trustee_payments.py``) are
    folded into ``total_paid`` and ``last_payment_date`` here, per explicit
    instruction, because from the *contract's* point of view a trustee
    payment is still money the contract received and still evidence the
    contract is active — the four-status classification below answers "is
    this contract moving", not "did the employer's own budget pay for it".
    This is the ONLY place trustee payments are ever combined with regular
    payments: ``calculate_real_balance`` and every other employer
    balance/credit calculation in this module deliberately never reference
    ``TrusteePayment`` — trustee amounts must never be deducted from an
    employer's mandate/deposit balance. ``Payment`` and ``TrusteePayment``
    are aggregated in separate pre-grouped subqueries before being outer
    joined to ``Contract`` (not joined directly against each other), so a
    contract with both regular and trustee payments never fans out into a
    row-count cross product that would corrupt the ``SUM``/``MAX``/``COUNT``
    aggregates — each subquery yields at most one row per contract before
    the join. ``TrusteePayment`` has no ``payment_date`` column at all (only
    ``notification_date``), so its contribution to ``last_payment_date`` is
    always via the notification date.

    Four mutually exclusive statuses, in priority order:
      1. ``"خاتمه‌یافته"`` (Completed) — confirmed payments cover the
         contract's ``total_amount``.
      2. ``"آغاز نشده"`` (Not Started) — no payment has ever been recorded
         against the contract.
      3. ``"راکد"`` (Dormant) — at least one payment exists, the contract
         is not completed, and no payment has landed in the last
         ``dormant_days_threshold`` days. This is the category the
         dashboard's name refers to, and the one relevant to Tabsare 2
         Madde 5 credit-transfer review.
      4. ``"فعال"`` (Active) — at least one payment exists, the contract
         is not completed, and the most recent payment is within
         ``dormant_days_threshold`` days.

    Args:
        db: Active SQLAlchemy database session.
        since_jalali_year: Jalali year of ``Contract.contract_date`` used as
            the inclusion cutoff (default 1402).
        dormant_days_threshold: Elapsed days since the last payment beyond
            which a contract with payment history is considered dormant
            (default 365, i.e. one calendar year).
        as_of: Reference date for the elapsed-days calculation; defaults to
            today.

    Returns:
        A tuple of:
          - A DataFrame, one row per in-scope contract, with columns
            ``tracking_code``, ``title``, ``employer_name``,
            ``university_name``, ``contract_date``, ``contract_jalali_year``,
            ``total_amount``, ``total_paid`` (regular + trustee payments
            combined), ``trustee_paid_amount`` (the trustee-only portion of
            ``total_paid``, broken out for auditability — ``0.0`` when the
            contract has no trustee payments), ``remaining_amount``,
            ``last_payment_date``, ``days_since_last_payment``, ``status``,
            ``data_quality_flag``.
          - A metadata dict: ``as_of``, ``since_jalali_year``,
            ``dormant_days_threshold``, ``excluded_no_contract_date``
            (in-scope-by-everything-else contracts skipped because
            ``contract_date`` is ``NULL`` and their Jalali year cannot be
            determined — not included in the DataFrame at all),
            ``missing_payment_date_flags`` (contracts that do have payment
            rows but none carry a usable ``payment_date`` or
            ``notification_date`` from either ``payments`` or
            ``trustee_payments`` — classified conservatively as ``"راکد"``
            since recency cannot be proven at all; see
            Docs/SATE_Living_Documentation.md §4.4 on legacy rows with a
            ``NULL`` ``payment_date``), and ``contracts_with_trustee_payment``
            (count of in-scope contracts that have at least one trustee
            payment attributed to them).
    """
    as_of = as_of or date.today()

    payment_agg = (
        select(
            Payment.contract_tracking_code.label("contract_tracking_code"),
            func.coalesce(func.sum(Payment.amount), 0).label("total_paid"),
            func.max(
                func.coalesce(Payment.payment_date, Payment.notification_date)
            ).label("last_payment_date"),
            func.count(Payment.tracking_code).label("payment_count"),
        )
        .where(Payment.is_deleted == False)
        .group_by(Payment.contract_tracking_code)
        .subquery()
    )

    trustee_agg = (
        select(
            TrusteePayment.contract_tracking_code.label("contract_tracking_code"),
            func.coalesce(func.sum(TrusteePayment.amount), 0).label("trustee_paid"),
            func.max(TrusteePayment.notification_date).label(
                "last_trustee_payment_date"
            ),
            func.count(TrusteePayment.id).label("trustee_payment_count"),
        )
        .where(TrusteePayment.is_deleted == False)
        .group_by(TrusteePayment.contract_tracking_code)
        .subquery()
    )

    statement = (
        select(
            Contract.tracking_code,
            Contract.title,
            Contract.contract_date,
            Contract.total_amount,
            Employer.name.label("employer_name"),
            University.name.label("university_name"),
            func.coalesce(payment_agg.c.total_paid, 0).label("total_paid"),
            payment_agg.c.last_payment_date,
            func.coalesce(payment_agg.c.payment_count, 0).label("payment_count"),
            func.coalesce(trustee_agg.c.trustee_paid, 0).label("trustee_paid"),
            trustee_agg.c.last_trustee_payment_date,
            func.coalesce(trustee_agg.c.trustee_payment_count, 0).label(
                "trustee_payment_count"
            ),
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
        .outerjoin(
            payment_agg,
            payment_agg.c.contract_tracking_code == Contract.tracking_code,
        )
        .outerjoin(
            trustee_agg,
            trustee_agg.c.contract_tracking_code == Contract.tracking_code,
        )
        .where(Contract.is_deleted == False)
    )

    rows = db.execute(statement).all()

    records = []
    excluded_no_contract_date = 0
    missing_payment_date_flags = 0
    contracts_with_trustee_payment = 0

    for row in rows:
        if row.contract_date is None:
            excluded_no_contract_date += 1
            continue

        jalali_year = to_jalali_date(row.contract_date).year
        if jalali_year < since_jalali_year:
            continue

        total_amount_val = float(row.total_amount or 0)
        regular_paid_val = float(row.total_paid or 0)
        trustee_paid_val = float(row.trustee_paid or 0)
        total_paid_val = regular_paid_val + trustee_paid_val
        payment_count_val = (row.payment_count or 0) + (
            row.trustee_payment_count or 0
        )
        if trustee_paid_val > 0:
            contracts_with_trustee_payment += 1

        candidate_dates = [
            d for d in (row.last_payment_date, row.last_trustee_payment_date) if d
        ]
        last_payment_date = max(candidate_dates) if candidate_dates else None

        data_quality_flag = None
        days_since_last_payment = None

        if total_amount_val > 0 and total_paid_val >= total_amount_val:
            status = "خاتمه‌یافته"
        elif payment_count_val == 0 or total_paid_val <= 0:
            status = "آغاز نشده"
        elif last_payment_date is None:
            status = "راکد"
            missing_payment_date_flags += 1
            data_quality_flag = (
                "دارای پرداخت ثبت‌شده بدون تاریخ معتبر — به صورت "
                "محافظه‌کارانه «راکد» طبقه‌بندی شد"
            )
        else:
            days_since_last_payment = (as_of - last_payment_date).days
            status = (
                "راکد"
                if days_since_last_payment > dormant_days_threshold
                else "فعال"
            )

        records.append(
            {
                "tracking_code": row.tracking_code,
                "title": row.title,
                "employer_name": row.employer_name,
                "university_name": row.university_name,
                "contract_date": row.contract_date,
                "contract_jalali_year": jalali_year,
                "total_amount": total_amount_val,
                "total_paid": total_paid_val,
                "trustee_paid_amount": trustee_paid_val,
                "remaining_amount": max(total_amount_val - total_paid_val, 0.0),
                "last_payment_date": last_payment_date,
                "days_since_last_payment": days_since_last_payment,
                "status": status,
                "data_quality_flag": data_quality_flag,
            }
        )

    columns = [
        "tracking_code",
        "title",
        "employer_name",
        "university_name",
        "contract_date",
        "contract_jalali_year",
        "total_amount",
        "total_paid",
        "trustee_paid_amount",
        "remaining_amount",
        "last_payment_date",
        "days_since_last_payment",
        "status",
        "data_quality_flag",
    ]
    df = pd.DataFrame.from_records(records, columns=columns)

    meta = {
        "as_of": as_of,
        "since_jalali_year": since_jalali_year,
        "dormant_days_threshold": dormant_days_threshold,
        "excluded_no_contract_date": excluded_no_contract_date,
        "missing_payment_date_flags": missing_payment_date_flags,
        "contracts_with_trustee_payment": contracts_with_trustee_payment,
    }
    return df, meta


EMPLOYER_KPI_TIERS = ("قرمز", "زرد", "سبز", "بدون تکلیف")


def get_employer_deposit_performance(
    db: Session,
    *,
    since_jalali_year: int = 1402,
    fiscal_years: Sequence[int] | None = None,
    red_threshold: float = 50.0,
    yellow_threshold: float = 80.0,
) -> pd.DataFrame:
    """
    Build the "درصد تحقق واریز" (deposit-realization %) performance table for
    the "داشبورد عملکرد مشمولین" (Employer KPI) dashboard — one row per
    employer, ranking compliance with their legal deposit mandate (اعتبار
    تکلیفی) and flagging under-performers ("دستگاه‌های متخلف" / red flags).

    This is a deliberately narrower metric than the "مانده واقعی" (real
    balance) used elsewhere in the app: it only compares deposits against
    the mandate (``deposit_amount / mandated_amount``), ignoring
    payments/transfers entirely, because the question here is "did this
    employer deposit what it legally owes", not "how much money is left to
    spend". Built on top of ``get_all_employers_financials`` (single source
    of truth for the per-employer/per-year mandate and deposit aggregates,
    including the existing Mother+Subsidiary roll-up), not a separate query,
    so this view can never drift from the numbers shown in the main
    dashboard's Tab 1/Tab 2.

    Args:
        db: Active SQLAlchemy database session.
        since_jalali_year: Lower bound (inclusive) on the fiscal year used
            when ``fiscal_years`` is not given (default 1402, matching the
            rest of the app's "data from 1402 onward" convention).
        fiscal_years: If given, restrict to exactly these fiscal years
            (e.g. a single year for a year-by-year view) instead of the
            open-ended ``since_jalali_year`` range — lets the caller compute
            either a single-year snapshot or a multi-year cumulative total
            by summing whichever years are selected.
        red_threshold: Realization-% cutoff (exclusive upper bound) for the
            "قرمز" (red flag) tier (default 50).
        yellow_threshold: Realization-% cutoff (exclusive upper bound) for
            the "زرد" tier, above ``red_threshold`` (default 80). Employers
            at or above this are "سبز".

    Returns:
        A DataFrame, one row per in-scope employer with any mandate/deposit
        activity, with columns: ``employer_code``, ``employer_name``,
        ``employer_type``, ``province``, ``mandated_amount``,
        ``deposit_amount``, ``shortfall_amount`` (``max(mandated - deposit,
        0)``), ``realization_pct`` (``None`` when ``mandated_amount`` is 0 —
        the ratio is undefined, not zero), and ``tier`` — one of
        :data:`EMPLOYER_KPI_TIERS`; an employer with no mandate in scope
        (``mandated_amount == 0``) is tiered ``"بدون تکلیف"`` rather than
        forced into a percentage tier it has no legal basis for.

        ``Subsidiary`` employers are excluded from the returned rows:
        ``get_all_employers_financials`` already rolls every Subsidiary's
        mandate/deposit figures up into its Mother's row (the same
        aggregation used everywhere else in the app), so a Subsidiary's own
        standalone row would either double-count money already reflected
        under its Mother or — far more often, since mandates are issued at
        the Mother/Independent level in practice — show up as meaningless
        ``"بدون تکلیف"`` noise in a list whose entire purpose is flagging
        real legal non-compliance. No figures are lost by this filter; they
        remain inside the Mother's aggregated row.
    """
    df_all = get_all_employers_financials(db)
    columns = [
        "employer_code",
        "employer_name",
        "employer_type",
        "province",
        "mandated_amount",
        "deposit_amount",
        "shortfall_amount",
        "realization_pct",
        "tier",
    ]
    if df_all.empty:
        return pd.DataFrame(columns=columns)

    df_scope = df_all[df_all["year"] >= since_jalali_year]
    if fiscal_years:
        df_scope = df_scope[df_scope["year"].isin(fiscal_years)]
    if df_scope.empty:
        return pd.DataFrame(columns=columns)

    grouped = df_scope.groupby(
        ["employer_code", "employer_name"], as_index=False
    )[["mandated_amount", "deposit_amount"]].sum()

    employer_rows = (
        db.query(
            Employer.classification_code,
            Employer.employer_type,
            Employer.province,
        )
        .filter(Employer.is_deleted == False)
        .all()
    )
    employer_meta = pd.DataFrame(
        employer_rows, columns=["employer_code", "employer_type", "province"]
    )
    grouped = grouped.merge(employer_meta, on="employer_code", how="left")

    def _tier_for(mandated: float, realization_pct) -> str:
        if mandated <= 0 or realization_pct is None:
            return "بدون تکلیف"
        if realization_pct < red_threshold:
            return "قرمز"
        if realization_pct < yellow_threshold:
            return "زرد"
        return "سبز"

    grouped["realization_pct"] = grouped.apply(
        lambda r: (r["deposit_amount"] / r["mandated_amount"] * 100)
        if r["mandated_amount"] > 0
        else None,
        axis=1,
    )
    grouped["shortfall_amount"] = (
        grouped["mandated_amount"] - grouped["deposit_amount"]
    ).clip(lower=0)
    grouped["tier"] = grouped.apply(
        lambda r: _tier_for(r["mandated_amount"], r["realization_pct"]), axis=1
    )

    grouped = grouped[grouped["employer_type"] != "Subsidiary"]

    return grouped[columns]


def get_employer_contract_activity(
    db: Session,
    *,
    since_jalali_year: int = 1402,
) -> tuple[pd.DataFrame, dict]:
    """
    Per-employer, per-year contract-signing and payment activity for the
    "عملکرد مشمولین" (Employer KPI) dashboard's contract-activity section:
    how many contracts an employer concluded each year, the combined value
    of those contracts, and how much was actually paid out (against any of
    that employer's contracts) that year.

    Mother employers are rolled up with their Subsidiaries (via
    ``_codes_to_include``, the same helper ``get_all_employers_financials``
    uses), matching the rollup convention used everywhere else in this
    module; standalone ``Subsidiary`` rows are excluded from the result for
    the same reason :func:`get_employer_deposit_performance` excludes them
    — their contracts/payments are already counted under their Mother.

    Two different "year" concepts intentionally share one ``year`` column:
      - ``contracts_count``/``contracts_amount`` are grouped by the Jalali
        year of ``Contract.contract_date`` (year the contract was signed).
      - ``payments_amount`` is grouped by ``Payment.funding_year`` (budget
        year), matching the ``funding_year`` convention used everywhere
        else in this app (§4.1 of the Living Documentation) — **not**
        necessarily the same contracts, since a contract signed in year Y
        can go on receiving payments in later years. Callers must not treat
        ``payments_amount`` as "how much of that year's contracts got
        paid"; it is "how much cash moved against this employer's
        contracts, budgeted to year Y" — a different, and not directly
        comparable, question. This function deliberately does not compute
        a payments/contracts ratio for this reason.

    Contracts with a ``NULL`` ``contract_date`` and payments with a
    ``NULL`` ``funding_year`` cannot be year-bucketed and are excluded,
    with counts surfaced in the returned metadata (see
    Docs/SATE_Living_Documentation.md §4.4 on known data-integrity gaps in
    these fields).

    Args:
        db: Active SQLAlchemy database session.
        since_jalali_year: Inclusive lower bound (Jalali year) applied
            independently to the contract-signing-year axis and the
            payment-funding-year axis (default 1402).

    Returns:
        A tuple of:
          - A DataFrame, one row per ``(employer, year)`` combination with
            any in-scope contract or payment activity, columns:
            ``employer_code``, ``employer_name``, ``employer_type``,
            ``year``, ``contracts_count``, ``contracts_amount``,
            ``payments_amount``.
          - A metadata dict: ``since_jalali_year``,
            ``excluded_no_contract_date``, ``excluded_no_funding_year``.
    """
    employers = (
        db.query(Employer)
        .filter(Employer.status == "Active", Employer.is_deleted == False)
        .all()
    )

    records = []
    excluded_no_contract_date = 0
    excluded_no_funding_year = 0

    for employer in employers:
        if employer.employer_type == "Subsidiary":
            continue

        codes = _codes_to_include(db, employer)

        contract_rows = (
            db.query(Contract.contract_date, Contract.total_amount)
            .filter(Contract.employer_code.in_(codes), Contract.is_deleted == False)
            .all()
        )
        contract_year_agg: dict[int, list] = {}
        for contract_date, total_amount in contract_rows:
            if contract_date is None:
                excluded_no_contract_date += 1
                continue
            year = to_jalali_date(contract_date).year
            if year < since_jalali_year:
                continue
            entry = contract_year_agg.setdefault(year, [0, 0.0])
            entry[0] += 1
            entry[1] += float(total_amount or 0)

        payment_rows = (
            db.query(Payment.funding_year, Payment.amount)
            .join(Contract, Payment.contract_tracking_code == Contract.tracking_code)
            .filter(
                Contract.employer_code.in_(codes),
                Payment.is_deleted == False,
                Contract.is_deleted == False,
            )
            .all()
        )
        payment_year_agg: dict[int, float] = {}
        for funding_year, amount in payment_rows:
            if funding_year is None:
                excluded_no_funding_year += 1
                continue
            if funding_year < since_jalali_year:
                continue
            payment_year_agg[funding_year] = payment_year_agg.get(
                funding_year, 0.0
            ) + float(amount or 0)

        all_years = set(contract_year_agg) | set(payment_year_agg)
        for year in all_years:
            count, contracts_amount = contract_year_agg.get(year, (0, 0.0))
            records.append(
                {
                    "employer_code": employer.classification_code,
                    "employer_name": employer.name,
                    "employer_type": employer.employer_type,
                    "year": year,
                    "contracts_count": count,
                    "contracts_amount": contracts_amount,
                    "payments_amount": payment_year_agg.get(year, 0.0),
                }
            )

    columns = [
        "employer_code",
        "employer_name",
        "employer_type",
        "year",
        "contracts_count",
        "contracts_amount",
        "payments_amount",
    ]
    df = pd.DataFrame.from_records(records, columns=columns)

    meta = {
        "since_jalali_year": since_jalali_year,
        "excluded_no_contract_date": excluded_no_contract_date,
        "excluded_no_funding_year": excluded_no_funding_year,
    }
    return df, meta


def get_employer_university_fund_flow(
    db: Session,
    *,
    since_jalali_year: int = 1402,
) -> tuple[pd.DataFrame, dict]:
    """
    Per ``(employer, university)`` pair: contract count/amount and payments
    actually received, for contracts concluded (``Contract.contract_date``,
    Jalali year) from ``since_jalali_year`` onward.

    This is the single base table for two different views in the
    "رتبه‌بندی دانشگاه‌ها" dashboard — the university ranking (group this by
    university) and the employer→university money-flow Sankey diagram (use
    the pairs directly) — kept as one function so the two views can never
    disagree with each other about the underlying numbers.

    Unlike :func:`get_employer_deposit_performance` and
    :func:`get_employer_contract_activity`, no Mother/Subsidiary roll-up is
    applied here: only ``Mother`` and ``Independent`` employers may hold a
    contract at all (§3.4's ``ALLOWED_CONTRACT_EMPLOYER_TYPES`` business
    rule, enforced in ``api/v1/endpoints/contracts.py`` and
    ``scripts/import_contracts_upsert.py``), so ``Contract.employer_code``
    is already the correct top-level holding entity for current and future
    data. Any pre-rule historical exception is surfaced as-is rather than
    silently merged into a parent, since misattributing it would be worse
    than showing it under its own (unusual) employer code.

    Args:
        db: Active SQLAlchemy database session.
        since_jalali_year: Inclusive lower bound (Jalali year) on
            ``Contract.contract_date`` (default 1402).

    Returns:
        A tuple of:
          - A DataFrame, one row per in-scope ``(employer, university)``
            pair with columns: ``employer_code``, ``employer_name``,
            ``university_id``, ``university_name``, ``province``,
            ``university_type``, ``contracts_count``, ``contracts_amount``,
            ``payments_amount``.
          - A metadata dict: ``since_jalali_year``,
            ``excluded_no_contract_date`` (contracts with a ``NULL``
            ``contract_date``, which cannot be year-scoped and are excluded
            entirely).
    """
    contract_rows = (
        db.query(
            Contract.tracking_code,
            Contract.contract_date,
            Contract.total_amount,
            Contract.university_id,
            Contract.employer_code,
        )
        .filter(Contract.is_deleted == False)
        .all()
    )

    pair_agg: dict[tuple, dict] = {}
    in_scope_codes = []
    excluded_no_contract_date = 0

    for tracking_code, contract_date, total_amount, university_id, employer_code in contract_rows:
        if contract_date is None:
            excluded_no_contract_date += 1
            continue
        year = to_jalali_date(contract_date).year
        if year < since_jalali_year:
            continue
        in_scope_codes.append(tracking_code)
        key = (employer_code, university_id)
        entry = pair_agg.setdefault(key, {"contracts_count": 0, "contracts_amount": 0.0})
        entry["contracts_count"] += 1
        entry["contracts_amount"] += float(total_amount or 0)

    payments_by_pair: dict[tuple, float] = {}
    if in_scope_codes:
        payment_rows = (
            db.query(
                Contract.employer_code,
                Contract.university_id,
                func.sum(Payment.amount),
            )
            .join(Payment, Payment.contract_tracking_code == Contract.tracking_code)
            .filter(
                Contract.tracking_code.in_(in_scope_codes),
                Payment.is_deleted == False,
            )
            .group_by(Contract.employer_code, Contract.university_id)
            .all()
        )
        payments_by_pair = {
            (employer_code, university_id): float(amount or 0)
            for employer_code, university_id, amount in payment_rows
        }

    employer_meta = {
        e.classification_code: e
        for e in db.query(Employer).filter(Employer.is_deleted == False).all()
    }
    university_meta = {
        u.national_id: u
        for u in db.query(University).filter(University.is_deleted == False).all()
    }

    records = []
    for (employer_code, university_id), agg in pair_agg.items():
        employer = employer_meta.get(employer_code)
        university = university_meta.get(university_id)
        records.append(
            {
                "employer_code": employer_code,
                "employer_name": employer.name if employer else employer_code,
                "university_id": university_id,
                "university_name": university.name if university else university_id,
                "province": university.province if university else None,
                "university_type": university.university_type if university else None,
                "contracts_count": agg["contracts_count"],
                "contracts_amount": agg["contracts_amount"],
                "payments_amount": payments_by_pair.get((employer_code, university_id), 0.0),
            }
        )

    columns = [
        "employer_code",
        "employer_name",
        "university_id",
        "university_name",
        "province",
        "university_type",
        "contracts_count",
        "contracts_amount",
        "payments_amount",
    ]
    df = pd.DataFrame.from_records(records, columns=columns)
    meta = {
        "since_jalali_year": since_jalali_year,
        "excluded_no_contract_date": excluded_no_contract_date,
    }
    return df, meta


def get_researcher_contract_activity(
    db: Session,
    *,
    since_jalali_year: int = 1402,
) -> tuple[pd.DataFrame, dict]:
    """
    Per researcher (طرح‌مجری/فناور): contract count/amount and payments
    actually received, for contracts concluded (``Contract.contract_date``,
    Jalali year) from ``since_jalali_year`` onward.

    Mirrors :func:`get_employer_university_fund_flow` (same scope rule --
    is_deleted rows and NULL-``contract_date`` contracts excluded, same
    Jalali-year cutoff) but aggregated by ``Contract.researcher_id`` instead
    of ``university_id``, for the "سمت عرضه" (supply-side) researcher
    ranking view. Kept as a separate function rather than reusing the same
    row set as the university view because the two group by a different key
    and a researcher's affiliated university/academic rank comes from
    ``models.researchers``, not ``models.university``.

    Args:
        db: Active SQLAlchemy database session.
        since_jalali_year: Inclusive lower bound (Jalali year) on
            ``Contract.contract_date`` (default 1402).

    Returns:
        A tuple of:
          - A DataFrame, one row per in-scope researcher with columns:
            ``researcher_national_code``, ``researcher_name``,
            ``academic_rank``, ``researcher_type``, ``university_id``,
            ``university_name``, ``province``, ``contracts_count``,
            ``contracts_amount``, ``payments_amount``.
          - A metadata dict: ``since_jalali_year``,
            ``excluded_no_contract_date``.
    """
    contract_rows = (
        db.query(
            Contract.tracking_code,
            Contract.contract_date,
            Contract.total_amount,
            Contract.researcher_id,
        )
        .filter(Contract.is_deleted == False)
        .all()
    )

    researcher_agg: dict[str, dict] = {}
    in_scope_codes = []
    excluded_no_contract_date = 0

    for tracking_code, contract_date, total_amount, researcher_id in contract_rows:
        if contract_date is None:
            excluded_no_contract_date += 1
            continue
        year = to_jalali_date(contract_date).year
        if year < since_jalali_year:
            continue
        in_scope_codes.append(tracking_code)
        entry = researcher_agg.setdefault(researcher_id, {"contracts_count": 0, "contracts_amount": 0.0})
        entry["contracts_count"] += 1
        entry["contracts_amount"] += float(total_amount or 0)

    payments_by_researcher: dict[str, float] = {}
    if in_scope_codes:
        payment_rows = (
            db.query(
                Contract.researcher_id,
                func.sum(Payment.amount),
            )
            .join(Payment, Payment.contract_tracking_code == Contract.tracking_code)
            .filter(
                Contract.tracking_code.in_(in_scope_codes),
                Payment.is_deleted == False,
            )
            .group_by(Contract.researcher_id)
            .all()
        )
        payments_by_researcher = {researcher_id: float(amount or 0) for researcher_id, amount in payment_rows}

    researcher_meta = {
        r.national_code: r
        for r in db.query(Researcher).filter(Researcher.is_deleted == False).all()
    }
    university_meta = {
        u.national_id: u
        for u in db.query(University).filter(University.is_deleted == False).all()
    }

    records = []
    for researcher_id, agg in researcher_agg.items():
        researcher = researcher_meta.get(researcher_id)
        university = university_meta.get(researcher.university_id) if researcher else None
        records.append(
            {
                "researcher_national_code": researcher_id,
                "researcher_name": researcher.full_name if researcher else researcher_id,
                "academic_rank": researcher.academic_rank if researcher else None,
                "researcher_type": researcher.researcher_type if researcher else None,
                "university_id": researcher.university_id if researcher else None,
                "university_name": university.name if university else None,
                "province": university.province if university else None,
                "contracts_count": agg["contracts_count"],
                "contracts_amount": agg["contracts_amount"],
                "payments_amount": payments_by_researcher.get(researcher_id, 0.0),
            }
        )

    columns = [
        "researcher_national_code",
        "researcher_name",
        "academic_rank",
        "researcher_type",
        "university_id",
        "university_name",
        "province",
        "contracts_count",
        "contracts_amount",
        "payments_amount",
    ]
    df = pd.DataFrame.from_records(records, columns=columns)
    meta = {
        "since_jalali_year": since_jalali_year,
        "excluded_no_contract_date": excluded_no_contract_date,
    }
    return df, meta


def get_mandate_by_employer_raw(
    db: Session, *, fiscal_years: Sequence[int] | None = None
) -> pd.DataFrame:
    """
    One row per employer with any mandate in ``fiscal_years``: its
    ``mandated_amount``/``deposit_amount`` summed across those years,
    alongside ``employer_type`` and ``province`` -- deliberately **not**
    rolled up (unlike :func:`get_all_employers_financials` /
    :func:`get_employer_deposit_performance`, where a Mother's row absorbs
    its Subsidiaries' figures).

    Geographic and structural breakdowns ("توزیع اعتبار تکلیفی به تفکیک
    استان", "سهم شرکت‌های مادر در مقابل زیرمجموعه") ask what each *legal
    entity* was mandated on its own -- a Subsidiary showing up under its own
    name/province/type is the whole point here, not something to collapse
    into its Mother. Reusing the rolled-up view would make every
    ``Subsidiary`` bucket read as ~0, hiding exactly the split this is
    meant to show.

    Args:
        db: Active SQLAlchemy database session.
        fiscal_years: Fiscal (Persian-calendar) years to sum over. Defaults
            to just the most recent year with any mandate in the table
            (a single-year snapshot, not all-time) -- pass an explicit list
            for a multi-year cumulative view.

    Returns:
        A DataFrame with columns: ``employer_code``, ``employer_name``,
        ``employer_type``, ``province``, ``mandated_amount``,
        ``deposit_amount`` (0 when the employer has no deposit receipts on
        file for the selected years).
    """
    if fiscal_years is None:
        latest = db.query(func.max(AnnualMandate.fiscal_year)).filter(
            AnnualMandate.is_deleted == False
        ).scalar()
        fiscal_years = [latest] if latest is not None else []

    mandate_rows = (
        db.query(
            Employer.classification_code,
            Employer.name,
            Employer.employer_type,
            Employer.province,
            func.sum(AnnualMandate.mandated_amount),
        )
        .select_from(AnnualMandate)
        .join(Employer, AnnualMandate.employer_code == Employer.classification_code)
        .filter(
            AnnualMandate.is_deleted == False,
            Employer.is_deleted == False,
            AnnualMandate.fiscal_year.in_(fiscal_years),
        )
        .group_by(
            Employer.classification_code, Employer.name,
            Employer.employer_type, Employer.province,
        )
        .all()
    )

    deposit_by_employer = dict(
        db.query(DepositReceipt.employer_code, func.sum(DepositReceipt.deposit_amount))
        .filter(
            DepositReceipt.is_deleted == False,
            DepositReceipt.fiscal_year.in_(fiscal_years),
        )
        .group_by(DepositReceipt.employer_code)
        .all()
    )

    records = [
        {
            "employer_code": code,
            "employer_name": name,
            "employer_type": employer_type,
            "province": province,
            "mandated_amount": float(mandated_amount or 0),
            "deposit_amount": float(deposit_by_employer.get(code, 0) or 0),
        }
        for code, name, employer_type, province, mandated_amount in mandate_rows
    ]
    columns = [
        "employer_code", "employer_name", "employer_type", "province",
        "mandated_amount", "deposit_amount",
    ]
    return pd.DataFrame.from_records(records, columns=columns)


def get_combined_pool_breakdown(db: Session) -> pd.DataFrame:
    """Bulk (one row per roll-up employer) version of
    :func:`calculate_gross_pool_balance` / :func:`calculate_combined_pool_balance`.

    Added 2026-10-13 for the Secretariat-vs-Fund balance sheet, which needs the
    combined position of ~250 employers at once (calling the single-employer
    functions would be 4 queries x N). The arithmetic is identical -- same
    :data:`TRANSFER_POOL_YEARS`, same Subsidiary -> parent roll-up for
    deposits and transfers-out, payments by the contract's own employer,
    transfers-in by destination -- and it was checked (2026-10-13) to agree
    with the single-employer functions for every employer.

    Index key ``employer_code`` is the *roll-up* employer: a Subsidiary's
    deposits and transfers-out are attributed to its ``parent_code``.

    Scope note (2026-10-16): this is the *whole-ledger* view (1402 through
    1405, :data:`ALL_FUND_YEARS`) because its consumer compares against the
    Fund's report, which does not separate 1405 from the earlier pools. So
    ``combined_balance`` here INCLUDES 1405 and differs from
    :func:`calculate_combined_pool_balance` (1402+1404, the transferable
    pool) by exactly ``balance_1405``; ``pool_balance`` is the figure that
    matches that function, and ``balance_1405`` matches
    :func:`calculate_balance_1405`.

    Columns (base Rials): ``deposit_1402``, ``deposit_1404_1405``,
    ``deposit_1405``, ``deposit_total``, ``expense_total``, ``expense_1405``,
    ``transfers_in``, ``transfers_out``, ``gross_balance`` (deposits -
    expense), ``combined_balance`` (after transfers, all years),
    ``pool_balance`` (1402+1404 after transfers), ``balance_1405``.
    """
    years = list(ALL_FUND_YEARS)

    employers = db.query(
        Employer.classification_code, Employer.parent_code
    ).filter(Employer.is_deleted == False).all()  # noqa: E712
    rollup = {code: (parent or code) for code, parent in employers}

    def series(rows) -> pd.Series:
        out: dict[str, float] = {}
        for key, amount in rows:
            root = rollup.get(key, key)
            out[root] = out.get(root, 0.0) + float(amount or 0)
        return pd.Series(out, dtype=float)

    def deposits_for(year_filter) -> pd.Series:
        return series(
            db.query(DepositReceipt.employer_code, func.sum(DepositReceipt.deposit_amount))
            .filter(
                DepositReceipt.is_deleted == False,  # noqa: E712
                year_filter(DepositReceipt.fiscal_year),
            )
            .group_by(DepositReceipt.employer_code)
            .all()
        )

    def expense_for(year_filter) -> pd.Series:
        return pd.Series(dict(
            db.query(Contract.employer_code, func.sum(Payment.amount))
            .join(Contract, Payment.contract_tracking_code == Contract.tracking_code)
            .filter(
                Payment.is_deleted == False,  # noqa: E712
                Payment.status.in_(("Final", "Draft")),
                Contract.is_deleted == False,  # noqa: E712
                year_filter(Payment.funding_year),
            )
            .group_by(Contract.employer_code)
            .all()
        ), dtype=float).astype(float)

    dep_1402 = deposits_for(lambda col: col == 1402)
    dep_1404_5 = deposits_for(lambda col: col.in_((1404, 1405)))
    dep_1405 = deposits_for(lambda col: col == CURRENT_YEAR_POOL)
    dep_total = deposits_for(lambda col: col.in_(years))

    expense = expense_for(lambda col: col.in_(years))
    expense_1405 = expense_for(lambda col: col == CURRENT_YEAR_POOL)

    # Transfers can only come from the pool years (enforced by the API).
    pool_years = list(TRANSFER_POOL_YEARS)
    transfers_out = series(
        db.query(CreditTransfer.source_employer_code, func.sum(CreditTransfer.amount))
        .filter(CreditTransfer.is_deleted == False, CreditTransfer.fiscal_year.in_(pool_years))  # noqa: E712
        .group_by(CreditTransfer.source_employer_code)
        .all()
    )
    transfers_in = pd.Series(dict(
        db.query(CreditTransfer.destination_employer_code, func.sum(CreditTransfer.amount))
        .filter(CreditTransfer.is_deleted == False, CreditTransfer.fiscal_year.in_(pool_years))  # noqa: E712
        .group_by(CreditTransfer.destination_employer_code)
        .all()
    ), dtype=float).astype(float)

    frame = pd.DataFrame({
        "deposit_1402": dep_1402,
        "deposit_1404_1405": dep_1404_5,
        "deposit_1405": dep_1405,
        "deposit_total": dep_total,
        "expense_total": expense,
        "expense_1405": expense_1405,
        "transfers_in": transfers_in,
        "transfers_out": transfers_out,
    }).fillna(0.0)
    frame["gross_balance"] = frame["deposit_total"] - frame["expense_total"]
    frame["combined_balance"] = frame["gross_balance"] + frame["transfers_in"] - frame["transfers_out"]
    frame["balance_1405"] = frame["deposit_1405"] - frame["expense_1405"]
    frame["pool_balance"] = frame["combined_balance"] - frame["balance_1405"]
    frame.index.name = "employer_code"
    return frame
