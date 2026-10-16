"""One-off report: دانشگاه سیستان و بلوچستان's SATE contract/payment activity.

Requested by Payam 2026-09-16: contract count, contract amount (million
Rial), the university's collaboration network (which SATE-mandated
employers it has contracted with, and their province), and amounts
actually received (payments), from 1402 onward -- as an Excel file to build
a PowerPoint from.

Reuses ``services.financial_engine.get_employer_university_fund_flow`` per
the project's standing rule (see the [[feedback_reuse_financial_formulas]]
memory) rather than re-deriving contract/payment aggregation from scratch.

Output: results/sistan_university_report_1402_1405.xlsx
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
from models.researchers import Researcher
from services.financial_engine import get_employer_university_fund_flow
from sqlalchemy import text

UNIVERSITY_ID = "14003058637"  # دانشگاه سیستان و بلوچستان
SINCE_YEAR = 1399
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "results" / "sistan_university_report_1399_1405.xlsx"
)
MILLION = 1_000_000

HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
TITLE_FONT = Font(bold=True, size=13, color="1F4E78")


def style_sheet(ws, df: pd.DataFrame, *, money_cols: list[str] | None = None) -> None:
    """Apply a consistent header/RTL/column-width/number-format pass."""
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
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            if col_name in money_cols:
                cell.number_format = "#,##0"

    for col_idx, col_name in enumerate(df.columns, start=1):
        max_len = max([len(str(col_name))] + [len(str(v)) for v in df[col_name]]) if len(df) else len(str(col_name))
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(max_len + 3, 12), 55)

    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 32


def build_report() -> dict[str, pd.DataFrame]:
    db = SessionLocal()
    try:
        flow_df, meta = get_employer_university_fund_flow(db, since_jalali_year=SINCE_YEAR)
        sistan = flow_df[flow_df["university_id"] == UNIVERSITY_ID].copy()

        # Contract-level detail (title, employer, researcher, date, status),
        # scoped the same way the reused function scopes its aggregate rows.
        contract_rows = (
            db.query(Contract, Employer, Researcher)
            .join(Employer, Contract.employer_code == Employer.classification_code)
            .outerjoin(Researcher, Contract.researcher_id == Researcher.national_code)
            .filter(Contract.university_id == UNIVERSITY_ID, Contract.is_deleted == False)  # noqa: E712
            .all()
        )

        contract_records, payment_records = [], []
        in_scope_tracking_codes = []
        for contract, employer, researcher in contract_rows:
            if contract.contract_date is None:
                continue
            jalali_year = to_jalali_date(contract.contract_date).year
            if jalali_year < SINCE_YEAR:
                continue
            in_scope_tracking_codes.append(contract.tracking_code)
            contract_records.append({
                "کد رهگیری قرارداد": contract.tracking_code,
                "مشمول (کارفرما)": employer.name,
                "استان مشمول": employer.province,
                "عنوان قرارداد": contract.title,
                "فناور": researcher.full_name if researcher else None,
                "سال انعقاد (شمسی)": jalali_year,
                "تاریخ انعقاد (میلادی)": contract.contract_date,
                "مدت اجرا (ماه)": contract.duration_months,
                "مبلغ قرارداد (میلیون ریال)": round(float(contract.total_amount) / MILLION),
                "وضعیت": contract.status,
            })

        if in_scope_tracking_codes:
            payment_rows = (
                db.query(Payment, Contract, Employer)
                .join(Contract, Payment.contract_tracking_code == Contract.tracking_code)
                .join(Employer, Contract.employer_code == Employer.classification_code)
                .filter(
                    Payment.contract_tracking_code.in_(in_scope_tracking_codes),
                    Payment.is_deleted == False,  # noqa: E712
                )
                .order_by(Payment.payment_date)
                .all()
            )
            for payment, contract, employer in payment_rows:
                payment_records.append({
                    "کد رهگیری پرداخت": payment.tracking_code,
                    "کد رهگیری قرارداد": contract.tracking_code,
                    "مشمول (کارفرما)": employer.name,
                    "عنوان قرارداد": contract.title,
                    "تاریخ پرداخت": payment.payment_date,
                    "سال پرداخت": payment.payment_year,
                    "سال مالی منبع": payment.funding_year,
                    "مبلغ پرداختی (میلیون ریال)": round(float(payment.amount) / MILLION),
                })

        contracts_df = pd.DataFrame(contract_records).sort_values("تاریخ انعقاد (میلادی)")
        payments_df = pd.DataFrame(payment_records)

        # شبکه همکاری: one row per counterparty employer.
        network_df = sistan[[
            "employer_name", "province", "contracts_count", "contracts_amount", "payments_amount",
        ]].rename(columns={
            "employer_name": "مشمول همکار",
            "province": "استان مشمول",
            "contracts_count": "تعداد قرارداد",
            "contracts_amount": "مبلغ قرارداد (میلیون ریال)",
            "payments_amount": "مبلغ دریافتی دانشگاه (میلیون ریال)",
        }).copy()
        network_df["مبلغ قرارداد (میلیون ریال)"] = (network_df["مبلغ قرارداد (میلیون ریال)"] / MILLION).round()
        network_df["مبلغ دریافتی دانشگاه (میلیون ریال)"] = (
            network_df["مبلغ دریافتی دانشگاه (میلیون ریال)"] / MILLION
        ).round()
        network_df = network_df.sort_values("مبلغ قرارداد (میلیون ریال)", ascending=False)

        # Year-by-year summary (contracts by signing year, payments by
        # payment year -- both are the natural "when did it happen" axis).
        by_contract_year = (
            contracts_df.groupby("سال انعقاد (شمسی)")
            .agg(تعداد_قرارداد=("کد رهگیری قرارداد", "count"), مبلغ_قرارداد=("مبلغ قرارداد (میلیون ریال)", "sum"))
            .reset_index()
            .rename(columns={"تعداد_قرارداد": "تعداد قرارداد", "مبلغ_قرارداد": "مبلغ قرارداد (میلیون ریال)"})
        )
        if not payments_df.empty:
            by_payment_year = (
                payments_df.groupby("سال پرداخت")
                .agg(مبلغ_دریافتی=("مبلغ پرداختی (میلیون ریال)", "sum"))
                .reset_index()
                .rename(columns={"سال پرداخت": "سال انعقاد (شمسی)", "مبلغ_دریافتی": "مبلغ دریافتی (میلیون ریال)"})
            )
        else:
            by_payment_year = pd.DataFrame(columns=["سال انعقاد (شمسی)", "مبلغ دریافتی (میلیون ریال)"])
        yearly_df = by_contract_year.merge(by_payment_year, on="سال انعقاد (شمسی)", how="outer").fillna(0)
        yearly_df = yearly_df.sort_values("سال انعقاد (شمسی)")

        total_contracts_amount = contracts_df["مبلغ قرارداد (میلیون ریال)"].sum() if not contracts_df.empty else 0
        total_payments_amount = payments_df["مبلغ پرداختی (میلیون ریال)"].sum() if not payments_df.empty else 0
        summary_df = pd.DataFrame([
            {"شاخص": "بازه زمانی", "مقدار": f"{SINCE_YEAR} تا کنون"},
            {"شاخص": "تعداد قراردادها", "مقدار": len(contracts_df)},
            {"شاخص": "مجموع مبلغ قراردادها (میلیون ریال)", "مقدار": round(total_contracts_amount)},
            {"شاخص": "مجموع مبلغ دریافتی دانشگاه (میلیون ریال)", "مقدار": round(total_payments_amount)},
            {
                "شاخص": "درصد جذب (دریافتی / کل قرارداد)",
                "مقدار": f"{(total_payments_amount / total_contracts_amount * 100):.1f}%"
                if total_contracts_amount else "—",
            },
            {"شاخص": "تعداد مشمولین همکار (شبکه همکاری)", "مقدار": len(network_df)},
        ])

        # Historical context: contracts before 1402, kept out of the main
        # scope per Payam's request but preserved so nothing is silently lost.
        pre_rows = (
            db.query(Contract, Employer, Researcher)
            .join(Employer, Contract.employer_code == Employer.classification_code)
            .outerjoin(Researcher, Contract.researcher_id == Researcher.national_code)
            .filter(Contract.university_id == UNIVERSITY_ID, Contract.is_deleted == False)  # noqa: E712
            .all()
        )
        pre_records = []
        for contract, employer, researcher in pre_rows:
            if contract.contract_date is None:
                continue
            jalali_year = to_jalali_date(contract.contract_date).year
            if jalali_year >= SINCE_YEAR:
                continue
            pre_records.append({
                "کد رهگیری قرارداد": contract.tracking_code,
                "مشمول (کارفرما)": employer.name,
                "عنوان قرارداد": contract.title,
                "فناور": researcher.full_name if researcher else None,
                "سال انعقاد (شمسی)": jalali_year,
                "مبلغ قرارداد (میلیون ریال)": round(float(contract.total_amount) / MILLION),
            })
        pre_df = pd.DataFrame(pre_records)

        return {
            "خلاصه": summary_df,
            "روند سالانه": yearly_df,
            "شبکه همکاری": network_df,
            "قراردادها (از 1402)": contracts_df,
            "پرداخت‌های دریافتی": payments_df,
            "قراردادهای قبل از 1402": pre_df,
        }
    finally:
        db.close()


def main() -> None:
    sheets = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    money_cols_by_sheet = {
        "خلاصه": [],
        "روند سالانه": ["مبلغ قرارداد (میلیون ریال)", "مبلغ دریافتی (میلیون ریال)"],
        "شبکه همکاری": ["مبلغ قرارداد (میلیون ریال)", "مبلغ دریافتی دانشگاه (میلیون ریال)"],
        "قراردادها (از 1402)": ["مبلغ قرارداد (میلیون ریال)"],
        "پرداخت‌های دریافتی": ["مبلغ پرداختی (میلیون ریال)"],
        "قراردادهای قبل از 1402": ["مبلغ قرارداد (میلیون ریال)"],
    }

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            style_sheet(writer.sheets[name], df, money_cols=money_cols_by_sheet.get(name, []))

    print(f"Generated: {OUTPUT_PATH}")
    print(sheets["خلاصه"].to_string(index=False))


if __name__ == "__main__":
    main()
