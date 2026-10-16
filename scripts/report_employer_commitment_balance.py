"""Per-employer commitment/free-balance report (Payam's request, 2026-10-04).

Answers: "برای هر شرکت، بابت قراردادهایی که بسته، در حال حاضر چقدر بدهکار
است؟" Worked example he gave (units: his "میلیارد تومان" example, applied
here in میلیون ریال like every other report in this project):
    قرارداد=2,000M  پرداخت‌شده=1,500M  واریزی=3,000M
    مانده شرکت      = واریزی − هزینه‌کرد کل           = 1,500M
    مانده تعهدات    = قرارداد − پرداخت‌شدهٔ همان قرارداد = 500M
    مانده آزاد       = مانده شرکت − مانده تعهدات         = 1,000M

One row per Mother/Independent employer (Subsidiary employers never hold
contracts/deposits of their own -- see models/employer.py -- so their
figures are already folded into their Mother via
``calculate_combined_pool_balance``, the same rolled-up function used
throughout the ATF reconciliation and dashboard work).

Column-by-column:
  - واریزی (۱۴۰۲+۱۴۰۴)، مانده کل شرکت: both via
    ``calculate_combined_pool_balance`` -- reused rather than re-derived,
    per [[feedback_reuse_financial_formulas]]. This already nets transfers
    at the combined-pool level per the 2026-09-16 redesign (not per single
    year), so "مانده" here is the employer's true current spendable
    position, not a stale single-year figure.
  - قرارداد / پرداخت‌شده: scoped to contracts signed (``contract_date``'s
    Jalali year) from 1402 onward, matching every other "از سال ۱۴۰۲"
    report in this project. "پرداخت‌شده" sums ALL payments ever made
    against those specific contracts (any funding_year/payment_year) --
    this is "how much of this signed contract has been disbursed", not a
    fiscal-year-scoped figure.

Caveat (documented in the notes sheet, not hidden): "مانده شرکت" nets
against ALL funding_year=1402/1404 payments system-wide, while
"مانده تعهدات" only counts payments against contracts signed since 1402.
If an employer has an older contract (signed before 1402) still being paid
from the 1402/1404 pool, "مانده آزاد" is money already spoken for by that
older contract and not actually free -- flagged per-row where it applies.

Output: results/employer_commitment_balance_report.xlsx
"""

import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal
from core.date_helper import to_jalali_date
from models.contract import Contract
from models.employer import Employer
from models.payment import Payment
from services.financial_engine import (
    TRANSFER_POOL_YEARS,
    calculate_balance_1405,
    calculate_combined_pool_balance,
)
from sqlalchemy import func

SINCE_YEAR = 1402
MILLION = 1_000_000
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "results" / "employer_commitment_balance_report.xlsx"

HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)


def style_sheet(ws, df: pd.DataFrame, *, money_cols: list[str] | None = None) -> None:
    ws.sheet_view.rightToLeft = True
    money_cols = money_cols or []
    for col_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row_idx, row in enumerate(df.itertuples(index=False), start=2):
        for col_idx, (col_name, value) in enumerate(zip(df.columns, row), start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if col_name in money_cols:
                cell.number_format = "#,##0"
    for col_idx, col_name in enumerate(df.columns, start=1):
        max_len = max([len(str(col_name))] + [len(str(v)) for v in df[col_name]]) if len(df) else len(str(col_name))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(max_len + 3, 12), 55)
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 30


def build_report() -> dict[str, pd.DataFrame]:
    db = SessionLocal()
    try:
        employers = (
            db.query(Employer)
            .filter(Employer.employer_type.in_(("Mother", "Independent")), Employer.is_deleted == False)  # noqa: E712
            .order_by(Employer.name)
            .all()
        )

        # Contracts signed since 1402, and payments against them -- both
        # fetched once and bucketed in Python rather than one query per
        # employer (this table is small enough that it's not worth N+1).
        contract_rows = (
            db.query(Contract.tracking_code, Contract.employer_code, Contract.contract_date, Contract.total_amount)
            .filter(Contract.is_deleted == False)  # noqa: E712
            .all()
        )
        in_scope_by_employer: dict[str, list[str]] = {}
        contract_amount_by_employer: dict[str, float] = {}
        for tracking_code, employer_code, contract_date, total_amount in contract_rows:
            if contract_date is None or to_jalali_date(contract_date).year < SINCE_YEAR:
                continue
            in_scope_by_employer.setdefault(employer_code, []).append(tracking_code)
            contract_amount_by_employer[employer_code] = (
                contract_amount_by_employer.get(employer_code, 0.0) + float(total_amount or 0)
            )

        all_in_scope_codes = [c for codes in in_scope_by_employer.values() for c in codes]
        paid_by_contract = dict(
            db.query(Payment.contract_tracking_code, func.sum(Payment.amount))
            .filter(Payment.contract_tracking_code.in_(all_in_scope_codes), Payment.is_deleted == False)  # noqa: E712
            .group_by(Payment.contract_tracking_code)
            .all()
        ) if all_in_scope_codes else {}

        # Contracts predating 1402 that are STILL being paid from the
        # 1402/1404 pool -- these eat into "مانده آزاد" without showing up
        # in "مانده تعهدات" (which is scoped to post-1402 contracts only).
        # Flagged per employer rather than silently absorbed into the
        # numbers.
        pre_1402_tracking_codes = [
            tracking_code
            for tracking_code, employer_code, contract_date, _ in contract_rows
            if contract_date is not None and to_jalali_date(contract_date).year < SINCE_YEAR
        ]
        pre_1402_payment_by_employer: dict[str, float] = {}
        if pre_1402_tracking_codes:
            rows = (
                db.query(Contract.employer_code, func.sum(Payment.amount))
                .join(Payment, Payment.contract_tracking_code == Contract.tracking_code)
                .filter(
                    Contract.tracking_code.in_(pre_1402_tracking_codes),
                    Payment.funding_year.in_(TRANSFER_POOL_YEARS),
                    Payment.is_deleted == False, Contract.is_deleted == False,  # noqa: E712
                )
                .group_by(Contract.employer_code)
                .all()
            )
            pre_1402_payment_by_employer = dict(rows)

        records = []
        for employer in employers:
            code = employer.classification_code
            deposit_and_balance = calculate_combined_pool_balance(db, code)

            in_scope = in_scope_by_employer.get(code, [])
            contracts_amount = contract_amount_by_employer.get(code, 0.0)
            paid_amount = sum(float(paid_by_contract.get(tc, 0) or 0) for tc in in_scope)
            committed_balance = contracts_amount - paid_amount

            # "مانده شرکت" from calculate_combined_pool_balance already
            # nets deposits minus ALL expense/transfer -- "مانده آزاد" is
            # what's left after also reserving the unpaid part of signed
            # contracts.
            free_balance = deposit_and_balance - committed_balance

            # Deposit alone (not net of expense), shown separately per
            # Payam's column list -- same combined-pool function, deposit
            # component only, computed directly for transparency.
            deposit_total = _combined_deposit_only(db, code)

            # 1405 credit is its own, non-transferable balance (2026-10-16):
            # shown beside the pool figure, never folded into it.
            balance_1405 = calculate_balance_1405(db, code)

            records.append({
                "شماره طبقه‌بندی": code,
                "نام شرکت": employer.name,
                "مجموع واریزی (۱۴۰۲ و ۱۴۰۴)": round(deposit_total / MILLION),
                "مانده کل شرکت (۱۴۰۲+۱۴۰۴)": round(deposit_and_balance / MILLION),
                "مانده ۱۴۰۵ (غیرقابل انتقال)": round(balance_1405 / MILLION),
                "مجموع مبالغ قراردادهای منعقدشده (از ۱۴۰۲)": round(contracts_amount / MILLION),
                "مجموع مبالغ پرداخت‌شده به قراردادها": round(paid_amount / MILLION),
                "مانده تعهدات شرکت": round(committed_balance / MILLION),
                "مانده آزاد شرکت": round(free_balance / MILLION),
                "هزینه‌کرد قراردادهای پیش از ۱۴۰۲ از محل استخر ۱۴۰۲/۱۴۰۴ (هشدار)": round(
                    pre_1402_payment_by_employer.get(code, 0.0) / MILLION
                ),
            })

        df = pd.DataFrame(records)
        df = df.sort_values("مانده آزاد شرکت", ascending=True)

        notes = pd.DataFrame({"یادداشت": [
            "همهٔ اعداد به میلیون ریال است (در مثال شما واحد میلیارد تومان بود؛ ۱ میلیارد تومان = ۱۰,۰۰۰ میلیون ریال).",
            "فرمول: مانده کل شرکت = واریزی منهای هزینه‌کرد کل (۱۴۰۲+۱۴۰۴، شامل انتقال اعتبار از محل تجمیعی -- "
            "همان calculate_combined_pool_balance که برای مدیریت انتقال اعتبار هم استفاده می‌شود).",
            "مانده تعهدات = مجموع مبلغ قراردادهای منعقدشده از ۱۴۰۲ منهای مجموع پرداختی به همان قراردادها "
            "(صرف‌نظر از سال مالی پرداخت).",
            "مانده آزاد = مانده کل شرکت منهای مانده تعهدات.",
            "مانده ۱۴۰۵ = واریزی ۱۴۰۵ منهای پرداخت‌هایی که سال مالی آن‌ها ۱۴۰۵ ثبت شده؛ اعتبار سال جاری قابل "
            "انتقال نیست و در «مانده کل شرکت» و «مانده آزاد» لحاظ نمی‌شود.",
            "یک نکتهٔ مهم: اگر شرکتی قرارداد قدیمی‌تر از ۱۴۰۲ دارد که هنوز از محل استخر ۱۴۰۲/۱۴۰۴ هزینه آن "
            "پرداخت می‌شود، آن هزینه در «مانده کل شرکت» کم شده ولی در «مانده تعهدات» (که فقط قراردادهای از "
            "۱۴۰۲ را می‌بیند) دیده نمی‌شود -- یعنی بخشی از «مانده آزاد» در واقع صرف همان قرارداد قدیمی شده و "
            "واقعاً آزاد نیست. ستون آخر این مبلغ را برای هر شرکت جداگانه نشان می‌دهد؛ هر شرکتی عدد غیرصفر دارد "
            "«مانده آزاد» او باید به همان مقدار کمتر در نظر گرفته شود.",
            "سطرها فقط مشمولین «مادر» و «مستقل» هستند -- زیرمجموعه‌ها (Subsidiary) قرارداد/واریزی مستقل ندارند "
            "و ارقامشان از قبل در شرکت مادر لحاظ شده (calculate_combined_pool_balance این رول‌آپ را انجام می‌دهد).",
        ]})

        return {"تطبیق تعهدات و مانده آزاد": df, "یادداشت‌ها": notes}
    finally:
        db.close()


def _combined_deposit_only(db, employer_code: str) -> float:
    """Deposit component alone (1402+1404 pool), rolled up Mother+Subsidiary
    the same way ``calculate_real_balance`` does -- used only to show the
    gross deposit figure next to the net balance, per Payam's column list."""
    from models.deposits import DepositReceipt

    return float(
        db.query(func.sum(DepositReceipt.deposit_amount))
        .join(Employer, DepositReceipt.employer_code == Employer.classification_code)
        .filter(
            (Employer.classification_code == employer_code) | (Employer.parent_code == employer_code),
            DepositReceipt.fiscal_year.in_(TRANSFER_POOL_YEARS),
            DepositReceipt.is_deleted == False, Employer.is_deleted == False,  # noqa: E712
        )
        .scalar() or 0
    )


def main() -> None:
    sheets = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    money_cols = [
        "مجموع واریزی (۱۴۰۲ و ۱۴۰۴)", "مانده کل شرکت (۱۴۰۲+۱۴۰۴)", "مانده ۱۴۰۵ (غیرقابل انتقال)",
        "مجموع مبالغ قراردادهای منعقدشده (از ۱۴۰۲)", "مجموع مبالغ پرداخت‌شده به قراردادها",
        "مانده تعهدات شرکت", "مانده آزاد شرکت",
        "هزینه‌کرد قراردادهای پیش از ۱۴۰۲ از محل استخر ۱۴۰۲/۱۴۰۴ (هشدار)",
    ]
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            style_sheet(writer.sheets[name], df, money_cols=money_cols if "یادداشت" not in name else [])

    print(f"Generated: {OUTPUT_PATH}")
    df = sheets["تطبیق تعهدات و مانده آزاد"]
    print(f"تعداد شرکت: {len(df)}")
    print(df[["شماره طبقه‌بندی", "نام شرکت", "مانده آزاد شرکت"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
