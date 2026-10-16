"""Reconcile the ATF Fund's (صندوق عتف) audit ledger against our database.

Source: an audit Excel Payam received from the Fund
(``حسابرسی 16 شهریور.xlsx``), which tracks a running per-employer cash
balance (deposits received minus payments disbursed) across 1402-1405.

=====================================================================
BUG FOUND AND FIXED 2026-09-15 -- read this before touching the formulas
=====================================================================
Payam caught a real contradiction: for employer 292390 (شرکت ملی مناطق
نفت‌خیز جنوب), the previous version of this script reported a 1404
expense of ~31,257M Rial, while the main dashboard's "ترازنامه مشمولین"
tab (``dashboard/app.py``'s ``get_employer_financials``) shows ~135,934M
for the same concept. Verified by direct query: this script had grouped
payments by ``Payment.payment_year`` (cash-disbursement date), while
"هزینه کرد سال مالی X" -- as Payam defined it explicitly -- means every
payment *funded from* fiscal year X's budget pool
(``Payment.funding_year``), regardless of which calendar year it was
actually disbursed in. ``payment_year=1404`` for 292390 is indeed
31,257,607,687; ``funding_year=1404`` is 135,934,201,020, matching the
dashboard exactly. **The database and dashboard were both right; this
script's field choice was the bug.** Every "هزینه/expense" figure below
now uses ``funding_year``, matching ``dashboard/app.py::get_employer_financials``
(the authoritative "داشبورد اصلی" reference Payam pointed to) --
including its Mother roll-up for payments via
``Contract.employer_code.in_(codes_to_include)``, which is a second,
independent roll-up bug fix (``services.financial_engine.calculate_real_balance``,
used in the previous version, does NOT roll up payments the same way --
harmless in practice only because subsidiaries structurally never hold
their own contracts).

Column design (per Payam's 2026-09-15 simplification request): one row
per Mother/Independent employer, with -- for each of fiscal years 1402
and 1404 -- deposit / expense (excl. transferred) / transferred expense /
balance, each shown for both "ما" (us, the database) and "صندوق" (the
Fund's file), plus a cumulative 1402+1404 balance and one final variance
column. All amounts in میلیون ریال (million Rials).

Fund-side column mapping (Sheet1, rolled up by Mother the same way as the
DB side -- the Fund's own file only merges 3 of our 26 Subsidiary
employers into their Mother, and even then drops one with no note at all;
this script re-derives the roll-up from Sheet1's raw per-code numbers
rather than trusting the Fund's partial manual merges):
  - واریزی 1402 ~= "مانده اعتبار ابتدای سال 1403" (the Fund's file has no
    separate gross-deposit column for 1402; this assumes no spending
    happened within 1402 itself, which the "هزینه" columns only start
    counting from 1403 -- consistent with Payam's own confirmation that
    1402 deposits were the mandate year and spending began after)
  - هزینه 1402 (excl. transfer) = "هزینه در سال 1403" + "مجموع هزینه کرد
    در سال 1404 از محل منابع 1402" (both years' spending drawn from the
    1402 pool, matching "هزینه کرد سال مالی 1402" regardless of the
    calendar year disbursed)
  - مانده 1402 = "مانده اعتبار 1402 تا پایان لیست 22..." (authoritative,
    taken directly rather than re-derived)
  - واریزی 1404 = "واریزی بابت بند ث تبصره 4 -1404" + "واریزی بابت ماده 65
    ... سال 1405" (small, 7 rows non-zero)
  - هزینه 1404 (excl. transfer) = "هزینه کرد بعد از ابلاغ اصلاحیه بند 2
    تبصره 5..." + the 5 calendar-1405 spending batches ("هزینه در سال 1405
    تا تاریخ 10 خرداد", "هزینه", "هزینه.1", "هزینه.2", "هزینه.3") -- all
    funded from the 1404 pool
  - انتقالی 1404 = "هزینه‌کرد بابت اصلاحیه بند 2 تبصره 5 سال
    1404_منظور هزینه‌های انتقال یافته است." (sparse -- only 1 of 276 rows
    has a value; the Fund's file barely tracks this compared to our full
    CreditTransfer records)
  - مانده 1404 = واریزی 1404 − هزینه 1404 − انتقالی 1404 (derived; equals
    the Fund's own "مانده اعتبار 1404" on every row except 227000, see the
    comment above COL_DEPOSIT_1405)

Output: results/atf_reconciliation_1402_1404.xlsx
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal
from models.contract import Contract
from models.deposits import DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.transfer import CreditTransfer
from sqlalchemy import func

AUDIT_FILE = Path(r"C:\Users\Payam\Downloads\تطبیق حسابرسی\حسابرسی 16 شهریور.xlsx")
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "results" / "atf_reconciliation_1402_1404.xlsx"
MILLION = 1_000_000

# The Fund's running ledger folds 1405 deposits (ماده 65) and 1405 spending
# into the same pool as 1404 (see the comment above COL_DEPOSIT_1405), while
# our DB tags them fiscal_year/funding_year=1405 (~88,017M deposits, ~1,000M
# payments as of 2026-09-15). The DB-side "1404" columns include 1405 too,
# so both sides describe the same pool.
YEARS_1402 = (1402,)
YEARS_1404 = (1404, 1405)

COL_OPENING_1403 = "مانده اعتبار ابتدای سال 1403\nریال"
COL_EXPENSE_1403 = "هزینه در سال 1403"
COL_EXPENSE_1404_FROM_1402 = "مجموع هزینه کرد در سال 1404 از محل منابع 1402"
COL_BALANCE_1402 = "مانده اعتبار 1402 تا پایان لیست 22 سال 1404 (شارژ صندوق 1404 محاسبه نشده است)"
COL_DEPOSIT_1404 = "واریزی بابت بند ث تبصره 4 -1404 "
COL_EXPENSE_1404 = (
    "هزینه کرد بعد از ابلاغ اصلاحیه بند 2 تبصره 5 تا پایان سال 1404_منظور هزینه کرد در سال 1404 از محل منابع سال 1404"
)
# Third fix (applied 2026-09-15): COL_EXPENSE_1404 alone UNDER-counts
# "هزینه کرد سال مالی 1404". The Fund also spends 1404-pool money in
# calendar 1405, tracked across the 5 COLS_EXPENSE_1405_FROM_1404 batches
# (sequential disbursements after the 10 Khordad cutoff), plus a small
# 1405 deposit column. Per-row identity verified (residual 0.0 Rial on
# every Sheet1 row of the 16 Shahrivar file):
#     "مانده اعتبار 1404 " (col18) == "مانده لحاظ شده ابتدای سال 1405" (col10)
#         + COL_DEPOSIT_1405 - sum(COLS_EXPENSE_1405_FROM_1404) - COL_TRANSFER_1404
# col10 equals "مانده 1404 (مابه التفاوت...)" (col9 = col7 - col8) on every row except
# 227000 (ساتکاب), where the Fund carried that row's 6B 1402 balance into
# the 1405 opening -- so col18 is the 1404-pool balance, NOT 1402+1404.
# The fund-side 1404 balance is therefore derived from components below,
# not read from col9 (which silently drops the 1405-dated spending). The
# DB side needs no change: `Payment.funding_year == 1404` already includes
# payments disbursed in calendar 1405.
COL_DEPOSIT_1405 = "واریزی بابت ماده 65 ضوابط اجرایی قانون بودجه سال 1405"
COLS_EXPENSE_1405_FROM_1404 = ["هزینه در سال 1405 تا  تاریخ 10 خرداد", "هزینه", "هزینه.1", "هزینه.2", "هزینه.3"]
COL_TRANSFER_1404 = "هزینه‌کرد بابت اصلاحیه بند 2 تبصره 5 سال 1404_منظور هزینه های انتقال یافته است."
COL_END_BALANCE_1404 = "مانده اعتبار 1404 "


def _employer_map(db):
    """code -> (effective_code, name); effective_code is the Mother's code
    for a Subsidiary, else the employer's own code."""
    employers = db.query(Employer).filter(Employer.is_deleted == False).all()  # noqa: E712
    return {
        e.classification_code: (
            e.parent_code if e.employer_type == "Subsidiary" and e.parent_code else e.classification_code,
            e.name,
        )
        for e in employers
    }


def _load_fund_rolled_up(emp_map: dict) -> pd.DataFrame:
    s1 = pd.read_excel(AUDIT_FILE, sheet_name="Sheet1")
    s1["employer_code"] = s1["شماره طبقه بندی"].astype(str).str.strip()
    s1["effective_code"] = s1["employer_code"].map(lambda c: emp_map.get(c, (c, None))[0])

    value_cols = [
        COL_OPENING_1403, COL_EXPENSE_1403, COL_EXPENSE_1404_FROM_1402, COL_BALANCE_1402,
        COL_DEPOSIT_1404, COL_DEPOSIT_1405, COL_EXPENSE_1404, *COLS_EXPENSE_1405_FROM_1404,
        COL_TRANSFER_1404, COL_END_BALANCE_1404,
    ]
    for col in value_cols:
        s1[col] = pd.to_numeric(s1[col], errors="coerce").fillna(0)

    subsidiary_counts = (s1["employer_code"] != s1["effective_code"]).groupby(s1["effective_code"]).sum()
    names = s1[s1["employer_code"] == s1["effective_code"]].set_index("effective_code")["عنوان مشمول"]

    rolled = s1.groupby("effective_code")[value_cols].sum()
    rolled["fund_name"] = names
    rolled["subsidiary_count"] = subsidiary_counts

    rolled["fund_deposit_1402"] = rolled[COL_OPENING_1403]
    rolled["fund_expense_1402"] = rolled[COL_EXPENSE_1403] + rolled[COL_EXPENSE_1404_FROM_1402]
    rolled["fund_transfer_1402"] = 0.0
    rolled["fund_deposit_1404"] = rolled[COL_DEPOSIT_1404] + rolled[COL_DEPOSIT_1405]
    rolled["fund_expense_1404"] = rolled[COL_EXPENSE_1404] + rolled[COLS_EXPENSE_1405_FROM_1404].sum(axis=1)
    rolled["fund_transfer_1404"] = rolled[COL_TRANSFER_1404]
    # Per-year balances (2026-09-16 restructuring, at Payam's explicit
    # request): NO transfer is netted into a single year's balance anymore.
    # A transfer is now purely a combined-pool concept (see
    # build_reconciliation's "تجمیعی" columns below) -- keeping it out of
    # the per-year figure is what actually fixes the failure mode that
    # prompted this: a data error in one year's deposit figure could make a
    # real, legitimate transfer look like it overdrew that single year, even
    # though the employer's combined 1402+1404 position covered it easily.
    rolled["fund_balance_1402"] = rolled["fund_deposit_1402"] - rolled["fund_expense_1402"]
    rolled["fund_balance_1404"] = rolled["fund_deposit_1404"] - rolled["fund_expense_1404"]
    return rolled


def _db_rolled_up(effective_codes: set[str]) -> pd.DataFrame:
    """One row per Mother/Independent code, matching
    dashboard/app.py::get_employer_financials's own roll-up (Mother +
    its Subsidiaries, payments grouped by funding_year, not payment_year)."""
    db = SessionLocal()
    try:
        subs_by_mother: dict[str, list[str]] = {}
        for code, parent in db.query(Employer.classification_code, Employer.parent_code).filter(
            Employer.employer_type == "Subsidiary", Employer.is_deleted == False  # noqa: E712
        ).all():
            subs_by_mother.setdefault(parent, []).append(code)

        records = []
        for code in effective_codes:
            group = [code] + subs_by_mother.get(code, [])

            def deposit_sum(years):
                return db.query(func.sum(DepositReceipt.deposit_amount)).filter(
                    DepositReceipt.employer_code.in_(group),
                    DepositReceipt.fiscal_year.in_(years), DepositReceipt.is_deleted == False,  # noqa: E712
                ).scalar() or 0

            def expense_sum(years):
                return db.query(func.sum(Payment.amount)).join(
                    Contract, Payment.contract_tracking_code == Contract.tracking_code
                ).filter(
                    Contract.employer_code.in_(group), Payment.funding_year.in_(years),
                    Payment.is_deleted == False, Contract.is_deleted == False,  # noqa: E712
                ).scalar() or 0

            def transfer_out_sum(years):
                return db.query(func.sum(CreditTransfer.amount)).filter(
                    CreditTransfer.source_employer_code.in_(group),
                    CreditTransfer.fiscal_year.in_(years), CreditTransfer.is_deleted == False,  # noqa: E712
                ).scalar() or 0

            def transfer_in_sum(years):
                return db.query(func.sum(CreditTransfer.amount)).filter(
                    CreditTransfer.destination_employer_code.in_(group),
                    CreditTransfer.fiscal_year.in_(years), CreditTransfer.is_deleted == False,  # noqa: E712
                ).scalar() or 0

            dep_1402, dep_1404 = float(deposit_sum(YEARS_1402)), float(deposit_sum(YEARS_1404))
            exp_1402, exp_1404 = float(expense_sum(YEARS_1402)), float(expense_sum(YEARS_1404))
            tout_1402, tout_1404 = float(transfer_out_sum(YEARS_1402)), float(transfer_out_sum(YEARS_1404))
            tin_1402, tin_1404 = float(transfer_in_sum(YEARS_1402)), float(transfer_in_sum(YEARS_1404))

            records.append({
                "effective_code": code,
                "db_deposit_1402": dep_1402,
                "db_expense_1402": exp_1402,
                # No transfer netted per-year (see the matching comment in
                # _load_fund_rolled_up) -- transfers are combined-pool only.
                "db_balance_1402": dep_1402 - exp_1402,
                "db_deposit_1404": dep_1404,
                "db_expense_1404": exp_1404,
                "db_balance_1404": dep_1404 - exp_1404,
                "db_transfer_net": (tout_1402 + tout_1404) - (tin_1402 + tin_1404),
            })
    finally:
        db.close()
    return pd.DataFrame.from_records(records).set_index("effective_code")


def build_reconciliation() -> dict[str, pd.DataFrame]:
    db = SessionLocal()
    try:
        emp_map = _employer_map(db)
    finally:
        db.close()

    fund = _load_fund_rolled_up(emp_map)
    db_totals = _db_rolled_up(set(fund.index))
    db_names = {code: emp_map[code][1] for code in fund.index if code in emp_map}

    rows = []
    for code in sorted(fund.index):
        f = fund.loc[code]
        d = db_totals.loc[code] if code in db_totals.index else None

        def d_get(key):
            return float(d[key]) if d is not None else 0.0

        db_bal_1402, db_bal_1404 = d_get("db_balance_1402"), d_get("db_balance_1404")
        db_before = db_bal_1402 + db_bal_1404
        db_transfer_net = d_get("db_transfer_net")
        db_after = db_before - db_transfer_net

        fund_bal_1402, fund_bal_1404 = float(f["fund_balance_1402"]), float(f["fund_balance_1404"])
        fund_before = fund_bal_1402 + fund_bal_1404
        fund_transfer_net = float(f["fund_transfer_1402"]) + float(f["fund_transfer_1404"])
        fund_after = fund_before - fund_transfer_net

        rows.append({
            "کد طبقه‌بندی (مادر/مستقل)": code,
            "نام مشمول (صندوق)": f["fund_name"],
            "نام مشمول (دیتابیس)": db_names.get(code),
            "تعداد زیرمجموعه تجمیع‌شده": int(f["subsidiary_count"]),

            "واریزی 1402 - ما": d_get("db_deposit_1402") / MILLION,
            "واریزی 1402 - صندوق": f["fund_deposit_1402"] / MILLION,
            "هزینه کرد 1402 (بدون انتقالی) - ما": d_get("db_expense_1402") / MILLION,
            "هزینه کرد 1402 (بدون انتقالی) - صندوق": f["fund_expense_1402"] / MILLION,
            "مانده اعتبار 1402 - ما": db_bal_1402 / MILLION,
            "مانده اعتبار 1402 - صندوق": fund_bal_1402 / MILLION,

            "واریزی 1404 - ما": d_get("db_deposit_1404") / MILLION,
            "واریزی 1404 - صندوق": f["fund_deposit_1404"] / MILLION,
            "هزینه کرد 1404 (بدون انتقالی) - ما": d_get("db_expense_1404") / MILLION,
            "هزینه کرد 1404 (بدون انتقالی) - صندوق": f["fund_expense_1404"] / MILLION,
            "مانده اعتبار 1404 - ما": db_bal_1404 / MILLION,
            "مانده اعتبار 1404 - صندوق": fund_bal_1404 / MILLION,

            "مانده تجمیعی 1402+1404 (قبل از انتقال) - ما": db_before / MILLION,
            "مانده تجمیعی 1402+1404 (قبل از انتقال) - صندوق": fund_before / MILLION,
            "هزینه کرد انتقالی از محل تجمیعی - ما": db_transfer_net / MILLION,
            "هزینه کرد انتقالی از محل تجمیعی - صندوق": fund_transfer_net / MILLION,
            "مانده تجمیعی (بعد از انتقال) - ما": db_after / MILLION,
            "مانده تجمیعی (بعد از انتقال) - صندوق": fund_after / MILLION,
        })

    df = pd.DataFrame(rows)
    df["اختلاف مانده تجمیعی بعد از انتقال (صندوق - ما)"] = (
        df["مانده تجمیعی (بعد از انتقال) - صندوق"] - df["مانده تجمیعی (بعد از انتقال) - ما"]
    )
    df = df.sort_values(
        "اختلاف مانده تجمیعی بعد از انتقال (صندوق - ما)", key=lambda s: s.abs(), ascending=False
    )

    summary_metrics = [
        ("واریزی 1402", "واریزی 1402 - ما", "واریزی 1402 - صندوق"),
        ("هزینه کرد 1402 (بدون انتقالی)", "هزینه کرد 1402 (بدون انتقالی) - ما", "هزینه کرد 1402 (بدون انتقالی) - صندوق"),
        ("مانده اعتبار 1402", "مانده اعتبار 1402 - ما", "مانده اعتبار 1402 - صندوق"),
        ("واریزی 1404", "واریزی 1404 - ما", "واریزی 1404 - صندوق"),
        ("هزینه کرد 1404 (بدون انتقالی)", "هزینه کرد 1404 (بدون انتقالی) - ما", "هزینه کرد 1404 (بدون انتقالی) - صندوق"),
        ("مانده اعتبار 1404", "مانده اعتبار 1404 - ما", "مانده اعتبار 1404 - صندوق"),
        ("مانده تجمیعی 1402+1404 (قبل از انتقال)", "مانده تجمیعی 1402+1404 (قبل از انتقال) - ما", "مانده تجمیعی 1402+1404 (قبل از انتقال) - صندوق"),
        ("هزینه کرد انتقالی از محل تجمیعی", "هزینه کرد انتقالی از محل تجمیعی - ما", "هزینه کرد انتقالی از محل تجمیعی - صندوق"),
        ("مانده تجمیعی (بعد از انتقال)", "مانده تجمیعی (بعد از انتقال) - ما", "مانده تجمیعی (بعد از انتقال) - صندوق"),
    ]
    summary = pd.DataFrame([
        {
            "شاخص (میلیون ریال)": label,
            "مجموع ما": df[db_col].sum(),
            "مجموع صندوق": df[fund_col].sum(),
            "اختلاف (صندوق - ما)": df[fund_col].sum() - df[db_col].sum(),
        }
        for label, db_col, fund_col in summary_metrics
    ])

    notes = pd.DataFrame({"یادداشت": [
        "باگ اصلی رفع شد (۲۰۲۶-۰۹-۱۵): نسخهٔ قبلی «هزینه کرد» را بر اساس Payment.payment_year محاسبه کرده بود؛ "
        "طبق تعریف دقیق شما، «هزینه کرد سال مالی X» یعنی هر پرداختی که از محل بودجهٔ سال X تأمین شده "
        "(Payment.funding_year)، صرف‌نظر از سال تقویمی پرداخت واقعی. با این اصلاح، عدد 1404 برای کد 292390 "
        "از ۳۱,۲۵۸ به ۱۳۵,۹۳۴ میلیون ریال تغییر کرد و اکنون دقیقاً با تب «ترازنامه مشمولین» داشبورد اصلی یکی است.",
        "روش تجمیع مادر/زیرمجموعه نیز با get_employer_financials (داشبورد اصلی) یکسان‌سازی شد: پرداختی‌ها هم "
        "روی مجموعهٔ [مادر + همهٔ زیرمجموعه‌ها] جمع می‌شوند (نه فقط کد مادر به‌تنهایی).",
        "«واریزی 1402 - صندوق» چون فایل صندوق ستون جداگانه‌ای برای واریزی خام سال ۱۴۰۲ ندارد، از ستون "
        "«مانده اعتبار ابتدای سال ۱۴۰۳» گرفته شده -- این با فرض «هیچ هزینه‌ای در خودِ سال ۱۴۰۲ انجام نشده» "
        "معادل واریزی خام است (اولین ستون هزینهٔ صندوق هم «هزینه در سال ۱۴۰۳» است، نه ۱۴۰۲).",
        "«هزینه انتقالی» صندوق تقریباً هیچ داده‌ای ندارد (فقط ۱ ردیف از ۲۷۶ ردیف Sheet1 مقدار غیرصفر دارد)، "
        "در حالی‌که ما رکورد کامل CreditTransfer داریم (۱۴۰۲: ~۷۸۴ میلیارد، ۱۴۰۴: ~۴۲۶ میلیارد ریال در مجموع). "
        "این عدم تقارن، احتمالاً بخش مهمی از باقیماندهٔ اختلاف است -- در جلسه حتماً بپرسید انتقال اعتبارها را "
        "صندوق کجای فایلش ثبت می‌کند.",
        "اصلاح سوم (۲۰۲۶-۰۹-۱۵): «هزینه 1404 - صندوق» علاوه بر ستون «هزینه کرد بعد از ابلاغ اصلاحیه...»، "
        "۵ ستون هزینهٔ سال ۱۴۰۵ (هزینه در سال ۱۴۰۵ تا ۱۰ خرداد، هزینه، هزینه.1، هزینه.2، هزینه.3) را هم شامل "
        "می‌شود، چون از محل منابع ۱۴۰۴ پرداخت شده‌اند. «واریزی 1404 - صندوق» واریزی ماده ۶۵ سال ۱۴۰۵ را هم دارد. "
        "«مانده از 1404 - صندوق» = واریزی − هزینه − انتقالی، و با ستون «مانده اعتبار 1404» خود صندوق در همهٔ "
        "ردیف‌ها برابر است، به‌جز کد ۲۲۷۰۰۰ (ساتکاب) که صندوق ۶,۰۰۰ میلیون ریال ماندهٔ ۱۴۰۲ را به ابتدای ۱۴۰۵ "
        "منتقل کرده (این مبلغ اینجا در «مانده از 1402» حساب شده، نه ۱۴۰۴ -- پس دوبار شمرده نمی‌شود).",
        "برای تقارن با صندوق، ستون‌های «1404 - ما» هم واریزی‌های fiscal_year=1405 (~۸۸,۰۱۷ میلیون ریال، ماده ۶۵) "
        "و پرداختی‌های funding_year=1405 (~۱,۰۰۰ میلیون ریال) را شامل می‌شوند، چون صندوق این‌ها را در همان "
        "استخر ۱۴۰۴ ثبت کرده است.",
        "بازطراحی چهارم (۲۰۲۶-۰۹-۱۶، به درخواست صریح شما): انتقال اعتبار دیگر از محل یک سال مشخص (۱۴۰۲ یا "
        "۱۴۰۴) کسر نمی‌شود، بلکه فقط از محل «مانده تجمیعی» این دو سال با هم کسر می‌شود. علت: یک خطای داده در "
        "واریزی ۱۴۰۲ یک مشمول (انتقال گاز ایران، ۲۹۲۹۱۰) باعث شده بود انتقالی واقعی و مجاز آن، در تک‌سال ۱۴۰۲ "
        "بیش از مانده به‌نظر برسد، در حالی‌که مانده تجمیعی او کاملاً کافی بود. ستون‌های «مانده اعتبار 1402» و "
        "«مانده اعتبار 1404» اکنون کاملاً خالص (واریزی منهای هزینه، بدون هیچ انتقالی) هستند؛ همهٔ انتقالی‌ها "
        "(هم ما هم صندوق) فقط یک‌بار، در ردیف «هزینه کرد انتقالی از محل تجمیعی»، از مجموع دو سال کسر می‌شوند. "
        "این تغییر هم‌زمان در بک‌اند (services/financial_engine.py::calculate_combined_pool_balance) و در "
        "اعتبارسنجی ثبت انتقال اعتبار (api/v1/endpoints/transfers.py) اعمال شده تا از این پس ثبت انتقال‌های "
        "واقعی به همین دلیل رد نشود.",
        "توضیح (۲۰۲۶-۱۰-۱۶): در سامانهٔ ما «مانده تجمیعی قابل انتقال» فقط ۱۴۰۲+۱۴۰۴ است و اعتبار ۱۴۰۵ مانده‌ای "
        "جداست که قابل انتقال نیست (calculate_combined_pool_balance / calculate_balance_1405). این گزارش تطبیق "
        "ولی عمداً همچنان ۱۴۰۵ را در ستون‌های «1404 - ما» نگه می‌دارد، چون فایل صندوق ۱۴۰۵ را از ۱۴۰۴ جدا نمی‌کند.",
        "واریزی ۱۴۰۲ همهٔ مشمولین (۲۰۲۶-۰۹-۱۶) از فایل «واریزی 1402 مشمولین.xlsx» صندوق بازخوانی و اصلاح شد "
        "(۲۴ مشمول اصلاح، ۱۳۵ مشمول اصلاً رکورد ۱۴۰۲ نداشتند) -- scripts/fix_deposits_1402.py.",
        "همهٔ اعداد بر حسب میلیون ریال است.",
    ]})

    return {"خلاصه کلی": summary, "تطبیق تفصیلی (سطح مادر-مستقل)": df, "یادداشت‌ها": notes}


def main() -> None:
    sheets = build_reconciliation()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for name, sheet_df in sheets.items():
            sheet_df.to_excel(writer, sheet_name=name, index=False)

    print(f"Generated: {OUTPUT_PATH}")
    print("\n" + "=" * 90)
    print(sheets["خلاصه کلی"].to_string(index=False))
    print("=" * 90)
    print(f"\nتعداد ردیف (سطح مادر/مستقل): {len(sheets['تطبیق تفصیلی (سطح مادر-مستقل)'])}")


if __name__ == "__main__":
    main()
