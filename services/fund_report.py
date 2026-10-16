"""Secretariat-vs-Fund balance sheet (ترازنامه دبیرخانه و صندوق).

Puts OUR figures (from ``services.financial_engine``) next to THE FUND's
figures (the imported ``fund_report_*`` snapshot, see models/fund_report.py).

Fund side
---------
The Fund's own report is a static snapshot (through payment series 05-25).
To keep it moving in parallel with our data entry, what we entered AFTER the
snapshot is added on top of it:

* deposits : ``deposit_receipts.id > snapshot.baseline_deposit_receipt_id``
             with fiscal_year 1404/1405 (the Fund's «واریزی 1404 به بعد»)
* payments : payments whose series is after ``baseline_payment_series``
             (e.g. 05-26, 05-27 ...), any funding year.

Fund balance = اعتبار 1402-1403 + واریزی 1404 به بعد - پرداختی.
(The Fund's fee column is informational; the Fund does not deduct it.)
Credit transfers (انتقال اعتبار)
--------------------------------
The Fund only sees disbursements; it has no transfer mechanism. Our system
charges the FULL transferred amount to the source employer as spending (so
its balance is right) and then pays the contract out of the broker's /
destination employer's account. The Fund instead charges each disbursement
to the employer whose credit funded it -- i.e. to the source employer, and
only when it is actually paid (verified on 2026-10-13: the Fund's «پرداختی»
of the source employers exceeds ours by ~ the broker's payments).

So the like-for-like comparison with the Fund is on a **payments basis**:

    our balance (Fund basis) = gross balance (deposits - own payments)
                               - broker-contract payments attributed to the
                                 source employers (pro-rata to the transfer
                                 shares of each contract, capped at the
                                 transferred total)
                               + (the same amount credited back to the
                                 broker who owns the contract)

The difference between this and our post-transfer combined balance is the
**transferred-but-not-yet-paid credit** (commitment), shown separately.

All figures are rolled up to the financial employer (a Subsidiary's lines
belong to its ``parent_code``), exactly like our own balances.

Amounts are base Rials; use :data:`MILLION` to convert for display.
"""

from __future__ import annotations

import re

import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models.deposits import DepositReceipt
from models.employer import Employer
from models.fund_report import FundReportLine, FundReportSnapshot
from services.financial_engine import get_combined_pool_breakdown

MILLION = 1_000_000
FUND_DEPOSIT_YEARS = (1404, 1405)

_SERIES_RE = re.compile(r"^(\d+)-(\d+)$")


def _series_key(series: str | None):
    match = _SERIES_RE.match((series or "").strip())
    return (int(match.group(1)), int(match.group(2))) if match else None


def _transfer_attribution(db: Session, rollup: dict[str, str]):
    """Pro-rata attribution of broker-contract payments to source employers.

    Returns ``(shares, charged, credited)``:
      * ``shares``  : {contract_tracking_code: [(source_rollup_code, share)]}
      * ``charged`` : {source_rollup_code: payments attributed to it}
      * ``credited``: {contract owner rollup code: payments attributed away}
    A contract's attributed amount is capped at what was transferred for it.
    """
    from services.financial_engine import ALL_FUND_YEARS, TRANSFER_POOL_YEARS

    # Transfers only exist in the pool years; payments are compared with the
    # Fund's whole ledger, which does not separate 1405 from earlier pools.
    years = list(ALL_FUND_YEARS)
    transfer_rows = db.execute(text("""
        select t.contract_tracking_code, t.source_employer_code, sum(t.amount)
        from credit_transfers t
        where t.is_deleted = false and t.fiscal_year = any(:years)
        group by 1, 2
    """), {"years": list(TRANSFER_POOL_YEARS)}).fetchall()
    per_contract: dict[str, dict[str, float]] = {}
    for contract, source, amount in transfer_rows:
        root = rollup.get(source, source)
        per_contract.setdefault(contract, {})
        per_contract[contract][root] = per_contract[contract].get(root, 0.0) + float(amount or 0)

    paid_rows = db.execute(text("""
        select p.contract_tracking_code, c.employer_code, sum(p.amount)
        from payments p join contracts c on c.tracking_code = p.contract_tracking_code
        where p.is_deleted = false and c.is_deleted = false
          and p.status in ('Final', 'Draft') and p.funding_year = any(:years)
        group by 1, 2
    """), {"years": years}).fetchall()
    owner: dict[str, str] = {}
    paid: dict[str, float] = {}
    for contract, employer, amount in paid_rows:
        owner[contract] = rollup.get(employer, employer)
        paid[contract] = float(amount or 0)

    shares: dict[str, list[tuple[str, float]]] = {}
    charged: dict[str, float] = {}
    credited: dict[str, float] = {}
    for contract, by_source in per_contract.items():
        total = sum(by_source.values())
        if total <= 0:
            continue
        shares[contract] = [(src, amt / total) for src, amt in by_source.items()]
        attributed = min(paid.get(contract, 0.0), total)
        if attributed <= 0 or contract not in owner:
            continue
        for src, share in shares[contract]:
            charged[src] = charged.get(src, 0.0) + attributed * share
        credited[owner[contract]] = credited.get(owner[contract], 0.0) + attributed
    return shares, charged, credited


def get_latest_snapshot(db: Session) -> FundReportSnapshot | None:
    return (
        db.query(FundReportSnapshot)
        .filter(FundReportSnapshot.is_deleted == False)  # noqa: E712
        .order_by(FundReportSnapshot.id.desc())
        .first()
    )


def get_secretariat_fund_balance_sheet(db: Session, snapshot: FundReportSnapshot | None = None) -> pd.DataFrame:
    """One row per financial employer, ours and the Fund's side by side.

    Returns an empty frame when no Fund snapshot has been imported.
    """
    snapshot = snapshot or get_latest_snapshot(db)
    if snapshot is None:
        return pd.DataFrame()

    employers = {
        code: (name, etype, parent, upper, province)
        for code, name, etype, parent, upper, province in db.query(
            Employer.classification_code, Employer.name, Employer.employer_type,
            Employer.parent_code, Employer.upper_organization, Employer.province,
        ).filter(Employer.is_deleted == False).all()  # noqa: E712
    }
    rollup = {code: (info[2] or code) for code, info in employers.items()}

    ours = get_combined_pool_breakdown(db)

    # ----- Fund snapshot lines (rolled up) --------------------------------
    lines = db.query(FundReportLine).filter(
        FundReportLine.snapshot_id == snapshot.id, FundReportLine.is_deleted == False  # noqa: E712
    ).all()
    fund_rows: dict[str, dict] = {}
    for line in lines:
        root = rollup.get(line.employer_code, line.employer_code)
        row = fund_rows.setdefault(root, {
            "fund_credit_1402_1403": 0.0, "fund_deposit_snapshot": 0.0, "fund_paid_snapshot": 0.0,
            "fund_fee": 0.0, "fund_lines": [], "fund_agency": line.executive_agency,
        })
        row["fund_credit_1402_1403"] += float(line.credit_1402_1403)
        row["fund_deposit_snapshot"] += float(line.deposit_1404)
        row["fund_paid_snapshot"] += float(line.paid_1404_1405)
        row["fund_fee"] += float(line.fund_fee)
        row["fund_lines"].append(line.employer_code)
    fund = pd.DataFrame.from_dict(fund_rows, orient="index")
    if fund.empty:
        fund = pd.DataFrame(columns=[
            "fund_credit_1402_1403", "fund_deposit_snapshot", "fund_paid_snapshot",
            "fund_fee", "fund_lines", "fund_agency",
        ])

    # ----- what we entered after the snapshot ------------------------------
    new_dep: dict[str, float] = {}
    for code, amount in (
        db.query(DepositReceipt.employer_code, func.sum(DepositReceipt.deposit_amount))
        .filter(
            DepositReceipt.is_deleted == False,  # noqa: E712
            DepositReceipt.id > snapshot.baseline_deposit_receipt_id,
            DepositReceipt.fiscal_year.in_(FUND_DEPOSIT_YEARS),
        )
        .group_by(DepositReceipt.employer_code)
        .all()
    ):
        root = rollup.get(code, code)
        new_dep[root] = new_dep.get(root, 0.0) + float(amount or 0)

    shares, charged, credited = _transfer_attribution(db, rollup)

    base_key = _series_key(snapshot.baseline_payment_series)
    new_paid: dict[str, float] = {}
    pay_rows = db.execute(text("""
        select p.contract_tracking_code, c.employer_code, p.series, sum(p.amount)
        from payments p join contracts c on c.tracking_code = p.contract_tracking_code
        where p.is_deleted = false and c.is_deleted = false
          and p.status in ('Final', 'Draft') and p.series is not null
        group by 1, 2, 3
    """)).fetchall()
    for contract, employer, series, amount in pay_rows:
        key = _series_key(series)
        if key is None or base_key is None or key <= base_key:
            continue
        amount = float(amount or 0)
        # the Fund charges a disbursement to the employer that funded it
        if contract in shares:
            for src, share in shares[contract]:
                new_paid[src] = new_paid.get(src, 0.0) + amount * share
        else:
            root = rollup.get(employer, employer)
            new_paid[root] = new_paid.get(root, 0.0) + amount

    # ----- assemble --------------------------------------------------------
    codes = sorted(set(fund.index) | set(ours.index[(ours.abs().sum(axis=1) > 0)]))
    codes = [c for c in codes if employers.get(c, (None, "Mother"))[1] != "Subsidiary"]
    df = pd.DataFrame(index=pd.Index(codes, name="employer_code"))
    df["employer_name"] = [employers.get(c, (c,))[0] for c in codes]
    df["upper_organization"] = [employers.get(c, (None, None, None, None))[3] for c in codes]
    df["fund_agency"] = fund.reindex(codes)["fund_agency"]
    df["fund_line_codes"] = fund.reindex(codes)["fund_lines"].apply(
        lambda v: "، ".join(v) if isinstance(v, list) else ""
    )

    zero = lambda col: ours.reindex(codes)[col].fillna(0.0)  # noqa: E731
    # --- ours
    df["our_deposit_1402"] = zero("deposit_1402")
    df["our_deposit_1404_1405"] = zero("deposit_1404_1405")
    df["our_expense_total"] = zero("expense_total")
    df["our_transfers_net"] = zero("transfers_in") - zero("transfers_out")
    df["our_gross_balance"] = zero("gross_balance")
    df["our_paid_via_transfers"] = pd.Series(charged).reindex(codes).fillna(0.0)
    df["our_paid_for_others"] = pd.Series(credited).reindex(codes).fillna(0.0)
    df["our_combined_balance"] = zero("combined_balance")  # whole ledger 1402-1405, comparable to the Fund
    df["our_pool_balance"] = zero("pool_balance")  # 1402+1404 after transfers (the transferable pool)
    df["our_balance_1405"] = zero("balance_1405")  # 1405 own balance, not transferable
    # payments-basis balance: what the Fund can see (see module docstring)
    df["our_balance_fund_basis"] = (
        df["our_gross_balance"] - df["our_paid_via_transfers"] + df["our_paid_for_others"]
    )
    # credit transferred out but not yet paid to the contract (commitment)
    df["our_unpaid_transfers"] = (zero("transfers_out") - df["our_paid_via_transfers"]).clip(lower=0.0)
    # --- fund
    f = fund.reindex(codes)
    df["fund_credit_1402_1403"] = f["fund_credit_1402_1403"].fillna(0.0)
    df["fund_deposit_snapshot"] = f["fund_deposit_snapshot"].fillna(0.0)
    df["fund_new_deposit"] = pd.Series(new_dep).reindex(codes).fillna(0.0)
    df["fund_deposit_1404"] = df["fund_deposit_snapshot"] + df["fund_new_deposit"]
    df["fund_paid_snapshot"] = f["fund_paid_snapshot"].fillna(0.0)
    df["fund_new_paid"] = pd.Series(new_paid).reindex(codes).fillna(0.0)
    df["fund_paid"] = df["fund_paid_snapshot"] + df["fund_new_paid"]
    df["fund_fee"] = f["fund_fee"].fillna(0.0)
    df["fund_balance"] = df["fund_credit_1402_1403"] + df["fund_deposit_1404"] - df["fund_paid"]
    # --- differences (Fund - ours)
    df["diff_deposit_1404"] = df["fund_deposit_1404"] - df["our_deposit_1404_1405"]
    df["diff_balance"] = df["fund_balance"] - df["our_balance_fund_basis"]
    df["diff_balance_after_transfers"] = df["fund_balance"] - df["our_combined_balance"]
    df["in_fund_report"] = df.index.isin(fund.index)
    return df.reset_index()
