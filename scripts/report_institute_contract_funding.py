"""Funding-source report for موسسه تحقیقات سیاست علمی کشور's contracts
(employer 128342).

Requested by Payam 2026-10-12: the institute acts purely as a broker
(کارگزار) with no mandate/deposit of its own -- every one of its contracts
is funded entirely by credit transfers (اصلاحیه تبصره ۲) out of OTHER
employers' spare combined (1402+1404) balance. He wants, for each contract,
exactly which source employer(s) funded it, how much from each, and that
source employer's balance before and after transfers -- to verify every
contract is actually fully funded and that no source employer is
overdrawn.

Reuses ``calculate_gross_pool_balance`` (deposits minus expense, no
transfer netted) and ``calculate_combined_pool_balance`` (net of ALL of
that employer's transfers, not just this one contract) from
``services.financial_engine`` rather than re-deriving balance logic here.

Output: results/institute_contract_funding_report.xlsx
"""

import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal
from models.contract import Contract
from models.employer import Employer
from models.transfer import CreditTransfer
from services.financial_engine import (
    calculate_combined_pool_balance,
    calculate_gross_pool_balance,
)

INSTITUTE_CODE = "128342"  # موسسه تحقیقات سیاست علمی کشور
MILLION = 1_000_000
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "results" / "institute_contract_funding_report.xlsx"

# "شرکت‌های وابسته به وزارت صمت.docx" (Payam, 2026-10-12) -- the candidate
# source-employer pool for funding موسسه تحقیقات contracts via credit
# transfer. Matched to `employers.classification_code` by hand (4 of the 13
# names needed a spelling fix: ZWNJ/space variants, a since-renamed name,
# and a "لامرد" vs "المرد" typo) -- see the 2026-10-12 session notes.
MINISTRY_OF_INDUSTRY_CODES = {
    "230170": "شرکت سهامی تهیه و تولید مواد معدنی ایران",
    "295730": "شرکت گسترش معادن و صنایع معدنی طلای زرشوران",
    "286650": "شرکت بازآفرینی شهری ایران",
    "295710": "شرکت توسعه صنایع انرژی‌بر پارسیان جنوب",
    "293000": "شرکت سهامی منطقه ویژه صنایع معدنی و فلزی خلیج فارس",
    "257000": "شرکت مادر تخصصی سازمان صنایع کوچک و شهرک‌های صنعتی ایران",
    "294000": "شرکت سهامی تولید آلومینای ایران",
    "293350": "شرکت سهامی نمایشگاه‌های بین‌المللی جمهوری اسلامی ایران",
    "295720": "شرکت تلاشگران صنعتی معدنی لامرد و پارسیان (فایل: المرد)",
    "234500": "سازمان گسترش و نوسازی صنایع ایران - مادر تخصصی (ایدرو)",
    "295080": "صندوق حمایت از سرمایه‌گذاری صنایع کوچک (فایل: صندوق ضمانت)",
    "280960": "صندوق ضمانت صادرات ایران",
    "293940": "شرکت سهامی فولاد آذربایجان",
}

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
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
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
        contracts = (
            db.query(Contract)
            .filter(Contract.employer_code == INSTITUTE_CODE, Contract.is_deleted == False)  # noqa: E712
            .order_by(Contract.tracking_code)
            .all()
        )
        transfers = (
            db.query(CreditTransfer)
            .filter(
                CreditTransfer.contract_tracking_code.in_([c.tracking_code for c in contracts]),
                CreditTransfer.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        transfers_by_contract: dict[str, list[CreditTransfer]] = {}
        for t in transfers:
            transfers_by_contract.setdefault(t.contract_tracking_code, []).append(t)

        employer_names = {
            e.classification_code: e.name
            for e in db.query(Employer).filter(Employer.is_deleted == False).all()  # noqa: E712
        }

        # Balances computed once per source employer (not once per row) --
        # an employer funding several institute contracts would otherwise
        # be queried redundantly.
        source_codes = {t.source_employer_code for t in transfers}
        gross_balance = {code: calculate_gross_pool_balance(db, code) for code in source_codes}
        net_balance = {code: calculate_combined_pool_balance(db, code) for code in source_codes}

        detail_rows = []
        summary_rows = []
        for contract in contracts:
            contract_transfers = transfers_by_contract.get(contract.tracking_code, [])
            funded_total = sum(float(t.amount) for t in contract_transfers)

            if contract_transfers:
                for t in contract_transfers:
                    detail_rows.append({
                        "کد قرارداد": contract.tracking_code,
                        "عنوان قرارداد": contract.title,
                        "مبلغ قرارداد (میلیون ریال)": round(float(contract.total_amount) / MILLION),
                        "کارفرمای مبدأ": employer_names.get(t.source_employer_code, t.source_employer_code),
                        "کد کارفرمای مبدأ": t.source_employer_code,
                        "مبلغ انتقالی بابت این قرارداد (میلیون ریال)": round(float(t.amount) / MILLION),
                        "مانده تجمیعی کارفرمای مبدأ، بدون انتقال اعتبار (میلیون ریال)": round(
                            gross_balance[t.source_employer_code] / MILLION
                        ),
                        "مانده کارفرمای مبدأ پس از همهٔ انتقالی‌هایش (میلیون ریال)": round(
                            net_balance[t.source_employer_code] / MILLION
                        ),
                    })
            else:
                detail_rows.append({
                    "کد قرارداد": contract.tracking_code,
                    "عنوان قرارداد": contract.title,
                    "مبلغ قرارداد (میلیون ریال)": round(float(contract.total_amount) / MILLION),
                    "کارفرمای مبدأ": "⚠️ هنوز هیچ انتقال اعتباری ثبت نشده",
                    "کد کارفرمای مبدأ": None,
                    "مبلغ انتقالی بابت این قرارداد (میلیون ریال)": 0,
                    "مانده تجمیعی کارفرمای مبدأ، بدون انتقال اعتبار (میلیون ریال)": None,
                    "مانده کارفرمای مبدأ پس از همهٔ انتقالی‌هایش (میلیون ریال)": None,
                })

            shortfall = float(contract.total_amount) - funded_total
            summary_rows.append({
                "کد قرارداد": contract.tracking_code,
                "عنوان قرارداد": contract.title,
                "مبلغ قرارداد (میلیون ریال)": round(float(contract.total_amount) / MILLION),
                "تعداد کارفرمای تأمین‌کننده": len(contract_transfers),
                "مجموع انتقالی دریافتی (میلیون ریال)": round(funded_total / MILLION),
                "کسری تأمین (میلیون ریال)": round(shortfall / MILLION),
                "وضعیت تأمین": (
                    "بدون تأمین" if not contract_transfers
                    else ("کامل" if abs(shortfall) < 1 else ("بیش از نیاز" if shortfall < 0 else "ناقص"))
                ),
            })

        detail_df = pd.DataFrame(detail_rows)
        summary_df = pd.DataFrame(summary_rows)

        # Flag any source employer whose total institute-contract transfers
        # exceed what calculate_combined_pool_balance now reports as their
        # TRUE remaining balance (i.e. a transfer that, combined with
        # everything else they've since spent/transferred, has pushed them
        # negative) -- a quick red flag, not a hard error.
        overdrawn = [
            {
                "کارفرمای مبدأ": employer_names.get(code, code),
                "کد کارفرما": code,
                "مانده بدون انتقال (میلیون ریال)": round(gross_balance[code] / MILLION),
                "مانده پس از همهٔ انتقالی‌ها (میلیون ریال)": round(net_balance[code] / MILLION),
            }
            for code in source_codes
            if net_balance[code] < 0
        ]
        overdrawn_df = pd.DataFrame(overdrawn)

        notes = pd.DataFrame({"یادداشت": [
            "موسسهٔ تحقیقات سیاست علمی کشور (۱۲۸۳۴۲) اعتبار تکلیفی/واریزی خودش را ندارد؛ هر قرارداد آن باید "
            "۱۰۰٪ از محل انتقال اعتبار (اصلاحیهٔ تبصرهٔ ۲) از مانده تجمیعی سایر کارفرمایان تأمین شود.",
            "«مانده تجمیعی ... بدون انتقال اعتبار» = واریزی منهای هزینه‌کرد آن کارفرما (۱۴۰۲+۱۴۰۴، بدون کسر "
            "هیچ انتقالی) -- یعنی سقف واقعی پیش از هر انتقالی.",
            "«مانده کارفرمای مبدأ پس از همهٔ انتقالی‌هایش» شامل تمام انتقال‌های آن کارفرما (نه فقط بابت همین "
            "قرارداد) است -- چون همان calculate_combined_pool_balance است که برای مدیریت انتقال اعتبار هم "
            "استفاده می‌شود.",
            "اگر قراردادی بیش از یک کارفرمای مبدأ دارد، هر کدام یک ردیف جداگانه در شیت تفصیلی است.",
            "شیت «خلاصهٔ تأمین» وضعیت هر قرارداد را یکجا نشان می‌دهد: کامل / ناقص / بیش از نیاز / بدون تأمین.",
            "شیت «کارفرمایان با مانده منفی» کارفرماهایی را نشان می‌دهد که مانده‌شان پس از همهٔ انتقالی‌هایشان "
            "(نه فقط بابت این قراردادها) منفی شده -- نیازمند بررسی.",
            "همهٔ اعداد به میلیون ریال است.",
        ]})

        ministry_rows = []
        for code, docx_name in MINISTRY_OF_INDUSTRY_CODES.items():
            db_name = employer_names.get(code, docx_name)
            ministry_rows.append({
                "کد کارفرما": code,
                "نام کارفرما": db_name,
                "مانده تجمیعی بدون انتقال اعتبار (میلیون ریال)": round(calculate_gross_pool_balance(db, code) / MILLION),
                "مانده تجمیعی پس از همهٔ انتقالی‌ها (میلیون ریال)": round(calculate_combined_pool_balance(db, code) / MILLION),
            })
        ministry_df = pd.DataFrame(ministry_rows).sort_values(
            "مانده تجمیعی پس از همهٔ انتقالی‌ها (میلیون ریال)", ascending=False
        )

        # Candidate pool for a NEW contract (10 میلیارد تومان = 100,000M
        # Rial, Payam 2026-10-12) once the 13-company list proved short:
        # every other "Mother"/"Independent" employer under همان دستگاه
        # اجرایی ("وزارت صنعت، معدن و تجارت (صمت)"), excluding ایمیدرو
        # (231500, explicitly excluded by Payam) and the 13 already
        # considered. Exploratory only -- no transfer registered yet.
        NEW_CONTRACT_NEED = 100_000 * MILLION  # 10 میلیارد تومان
        EXCLUDED_FOR_CANDIDATE_SEARCH = set(MINISTRY_OF_INDUSTRY_CODES) | {"231500"}
        samt_employers = (
            db.query(Employer)
            .filter(
                Employer.upper_organization == "وزارت صنعت، معدن و تجارت (صمت)",
                Employer.employer_type.in_(("Mother", "Independent")),
                Employer.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        candidate_rows = []
        for e in samt_employers:
            if e.classification_code in EXCLUDED_FOR_CANDIDATE_SEARCH:
                continue
            net = calculate_combined_pool_balance(db, e.classification_code)
            if net <= 0:
                continue
            candidate_rows.append({
                "کد کارفرما": e.classification_code,
                "نام کارفرما": e.name,
                "مانده تجمیعی بدون انتقال اعتبار (میلیون ریال)": round(
                    calculate_gross_pool_balance(db, e.classification_code) / MILLION
                ),
                "مانده تجمیعی پس از همهٔ انتقالی‌های فعلی (میلیون ریال)": round(net / MILLION),
            })
        candidate_df = pd.DataFrame(candidate_rows).sort_values(
            "مانده تجمیعی پس از همهٔ انتقالی‌های فعلی (میلیون ریال)", ascending=False
        )
        total_candidate_balance = candidate_df[
            "مانده تجمیعی پس از همهٔ انتقالی‌های فعلی (میلیون ریال)"
        ].sum() * MILLION if not candidate_df.empty else 0
        ministry_13_total = ministry_df["مانده تجمیعی پس از همهٔ انتقالی‌ها (میلیون ریال)"].sum() * MILLION

        candidate_notes = pd.DataFrame({"یادداشت": [
            f"قرارداد جدید مورد نظر: ۱۰ میلیارد تومان = {NEW_CONTRACT_NEED // MILLION:,.0f} میلیون ریال.",
            f"مانده تجمیعی باقیمانده در همان ۱۳ شرکت قبلی (پس از انتقال‌های ثبت‌شده): "
            f"{ministry_13_total // MILLION:,.0f} میلیون ریال -- کمتر از نیاز.",
            f"کسری باقی‌مانده پس از مصرف کامل همان ۱۳ شرکت: "
            f"{(NEW_CONTRACT_NEED - ministry_13_total) // MILLION:,.0f} میلیون ریال.",
            f"⚠️ مجموع مانده تمام {len(candidate_df)} شرکت دیگر زیرمجموعهٔ وزارت صمت (بدون ایمیدرو، بدون ۱۳ "
            f"شرکت قبلی) فقط {total_candidate_balance // MILLION:,.0f} میلیون ریال است -- یعنی حتی با مصرف "
            "کامل همهٔ آن‌ها هم، این کسری پوشش داده نمی‌شود.",
            "ایمیدرو (۲۳۱۵۰۰) طبق دستور شما از این جست‌وجو کنار گذاشته شد؛ برای اطلاع، مانده تجمیعی آن به‌تنهایی "
            "بیش از ۲ هزار میلیارد ریال است -- در صورت نیاز، تنها گزینهٔ واقعی برای پوشش کامل این کسری در همین "
            "دستگاه (وزارت صمت) است.",
            "هیچ انتقال اعتباری در این مرحله ثبت نشده -- این شیت صرفاً برای بررسی و تصمیم‌گیری شماست.",
            "اعداد میلیون ریال.",
        ]})

        sheets = {"تفصیلی (قرارداد × کارفرما)": detail_df, "خلاصهٔ تأمین": summary_df}
        if not overdrawn_df.empty:
            sheets["کارفرمایان با مانده منفی"] = overdrawn_df
        sheets["مانده شرکت‌های وزارت صمت"] = ministry_df
        sheets["کاندیدای تکمیل مانده"] = candidate_df
        sheets["یادداشت کاندیدای تکمیل"] = candidate_notes
        sheets["یادداشت‌ها"] = notes
        return sheets
    finally:
        db.close()


def main() -> None:
    sheets = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    money_cols_by_sheet = {
        "تفصیلی (قرارداد × کارفرما)": [
            "مبلغ قرارداد (میلیون ریال)", "مبلغ انتقالی بابت این قرارداد (میلیون ریال)",
            "مانده تجمیعی کارفرمای مبدأ، بدون انتقال اعتبار (میلیون ریال)",
            "مانده کارفرمای مبدأ پس از همهٔ انتقالی‌هایش (میلیون ریال)",
        ],
        "خلاصهٔ تأمین": [
            "مبلغ قرارداد (میلیون ریال)", "مجموع انتقالی دریافتی (میلیون ریال)", "کسری تأمین (میلیون ریال)",
        ],
        "کارفرمایان با مانده منفی": ["مانده بدون انتقال (میلیون ریال)", "مانده پس از همهٔ انتقالی‌ها (میلیون ریال)"],
        "مانده شرکت‌های وزارت صمت": [
            "مانده تجمیعی بدون انتقال اعتبار (میلیون ریال)", "مانده تجمیعی پس از همهٔ انتقالی‌ها (میلیون ریال)",
        ],
        "کاندیدای تکمیل مانده": [
            "مانده تجمیعی بدون انتقال اعتبار (میلیون ریال)", "مانده تجمیعی پس از همهٔ انتقالی‌های فعلی (میلیون ریال)",
        ],
    }
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            style_sheet(writer.sheets[name], df, money_cols=money_cols_by_sheet.get(name, []))

    print(f"Generated: {OUTPUT_PATH}")
    summary = sheets["خلاصهٔ تأمین"]
    print(summary["وضعیت تأمین"].value_counts().to_string())


if __name__ == "__main__":
    main()
