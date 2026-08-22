"""Generate the DATA extract behind "Table 2" of the regulatory-letter
response (the official پیوست/annex template the user supplied, filled in
separately from this extract).

Template columns (from the user-supplied Word annex, 9 grid columns):

    1. طبقه‌بندی دستگاه            -> Employer.classification_code
    2. نام شرکت/بانک/... (کارفرما) -> Employer.name
    3. نام دانشگاه/...             -> University.name
    4. مبلغ مندرج در توافقنامه — طرح(پروژه)‌های کاربردی
    5. مبلغ مندرج در توافقنامه — طرح رساله‌های تحصیلات تکمیلی
    6. مبلغ مندرج در توافقنامه — جمع  (4 + 5)
    7. مبلغ پرداختی بابت — طرح(پروژه)‌های کاربردی
    8. مبلغ پرداختی بابت — طرح رساله‌های تحصیلات تکمیلی
    9. مبلغ پرداختی بابت — جمع  (7 + 8)

One row per (Employer, University) pair.

Scope (per explicit user instruction: "کاملا بر اساس داده‌های جدول ۱"):
  * Exactly the same underlying contracts/payments as Table 1 — i.e. every
    contract that received at least one ``payments`` (NOT
    ``trustee_payments`` — see Table 1 script's docstring for why) row with
    ``payment_year == PAYMENT_YEAR``. A contract's ``total_amount`` is
    counted once per contract (not once per payment row) toward columns
    4/5/6; its 1404 payments are summed toward columns 7/8/9.
  * Only active (``is_deleted == False``) rows throughout.

Project type split (no such field exists on ``contracts`` — the letter's
own two categories are reconstructed from contract value, per explicit
user instruction):
  * ``Contract.total_amount >= APPLIED_THRESHOLD_RIALS``  -> "کاربردی"
    (columns 4/7)
  * ``Contract.total_amount <  APPLIED_THRESHOLD_RIALS``  -> "رساله"
    (columns 5/8)
  Threshold: 40,000,000 Tomans = 400,000,000 Rials (base unit stored in
  the DB), confirmed with the user.

Output: results/regulatory_report_table2_1404_data.xlsx
  - Sheet "داده خام جدول ۲": the 9 columns above, one row per
    (employer, university) pair, ready to be dropped into the official
    Word annex.
  - Sheet "جزئیات قراردادها": per-contract detail (which type each
    contract was classified as, its amount, and its 1404 payment sum) —
    for sanity-checking the classification/aggregation before it goes into
    a regulatory submission.
"""

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from models.contract import Contract
from models.employer import Employer
from models.payment import Payment
from models.university import University


PAYMENT_YEAR = 1404
APPLIED_THRESHOLD_RIALS = 400_000_000  # 40,000,000 Tomans

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / f"regulatory_report_table2_{PAYMENT_YEAR}_data.xlsx"

TYPE_APPLIED = "کاربردی"
TYPE_THESIS = "رساله"

COL_CODE = "طبقه‌بندی دستگاه"
COL_EMPLOYER = "نام شرکت/بانک/موسسه انتفاعی وابسته به دولت (کارفرما)"
COL_UNIVERSITY = "نام دانشگاه/مؤسسه آموزش عالی و پژوهشی/جهاد دانشگاهی"
COL_AGR_APPLIED = "مبلغ توافقنامه - طرح کاربردی (ریال)"
COL_AGR_THESIS = "مبلغ توافقنامه - رساله تحصیلات تکمیلی (ریال)"
COL_AGR_TOTAL = "مبلغ توافقنامه - جمع (ریال)"
COL_PAY_APPLIED = "مبلغ پرداختی - طرح کاربردی (ریال)"
COL_PAY_THESIS = "مبلغ پرداختی - رساله تحصیلات تکمیلی (ریال)"
COL_PAY_TOTAL = "مبلغ پرداختی - جمع (ریال)"


def fetch_contract_level(db) -> pd.DataFrame:
    """One row per (contract, payment) — same base scope as Table 1."""
    query = (
        select(
            Employer.classification_code.label("employer_code"),
            Employer.name.label("employer_name"),
            University.national_id.label("university_id"),
            University.name.label("university_name"),
            Contract.tracking_code.label("contract_tracking_code"),
            Contract.title.label("contract_title"),
            Contract.total_amount.label("contract_total_amount"),
            Payment.tracking_code.label("payment_tracking_code"),
            Payment.amount.label("payment_amount"),
        )
        .select_from(Payment)
        .join(Contract, Payment.contract_tracking_code == Contract.tracking_code)
        .join(Employer, Contract.employer_code == Employer.classification_code)
        .join(University, Contract.university_id == University.national_id)
        .where(
            Payment.is_deleted == False,
            Contract.is_deleted == False,
            Employer.is_deleted == False,
            University.is_deleted == False,
            Payment.payment_year == PAYMENT_YEAR,
        )
    )
    rows = db.execute(query).all()
    return pd.DataFrame(rows, columns=[
        "employer_code", "employer_name", "university_id", "university_name",
        "contract_tracking_code", "contract_title", "contract_total_amount",
        "payment_tracking_code", "payment_amount",
    ])


def main() -> None:
    db = SessionLocal()
    try:
        raw = fetch_contract_level(db)
    finally:
        db.close()

    if raw.empty:
        print("No payments found for the given PAYMENT_YEAR — nothing to export.")
        return

    raw["contract_total_amount"] = raw["contract_total_amount"].astype(float)
    raw["payment_amount"] = raw["payment_amount"].astype(float)
    raw["project_type"] = raw["contract_total_amount"].apply(
        lambda amt: TYPE_APPLIED if amt >= APPLIED_THRESHOLD_RIALS else TYPE_THESIS
    )

    # Per-contract payment sum in PAYMENT_YEAR (a contract may have >1 payment row)
    contract_payment_sum = (
        raw.groupby("contract_tracking_code")["payment_amount"].sum()
    )

    # Distinct contracts (so total_amount is counted once each, not once per payment row)
    contracts = (
        raw.drop_duplicates(subset=["contract_tracking_code"])
        .set_index("contract_tracking_code")
        [["employer_code", "employer_name", "university_id", "university_name",
          "contract_title", "contract_total_amount", "project_type"]]
        .copy()
    )
    contracts["payment_1404_sum"] = contract_payment_sum

    # --- Sheet 2: per-contract detail, for sanity-checking ---
    detail_df = contracts.reset_index().rename(columns={
        "contract_tracking_code": "کد رهگیری قرارداد",
        "employer_code": "کد کارفرما",
        "employer_name": "نام کارفرما",
        "university_id": "شناسه دانشگاه",
        "university_name": "نام دانشگاه",
        "contract_title": "عنوان طرح",
        "contract_total_amount": "مبلغ قرارداد (ریال)",
        "project_type": "دسته‌بندی (بر اساس آستانه ۴۰۰ میلیون ریال)",
        "payment_1404_sum": f"مجموع پرداختی {PAYMENT_YEAR} (ریال)",
    }).sort_values(["نام کارفرما", "نام دانشگاه", "کد رهگیری قرارداد"])

    # --- Sheet 1: pivoted per (employer, university) ---
    pivot_agreement = contracts.pivot_table(
        index=["employer_code", "employer_name", "university_id", "university_name"],
        columns="project_type",
        values="contract_total_amount",
        aggfunc="sum",
        fill_value=0.0,
    )
    pivot_payment = contracts.pivot_table(
        index=["employer_code", "employer_name", "university_id", "university_name"],
        columns="project_type",
        values="payment_1404_sum",
        aggfunc="sum",
        fill_value=0.0,
    )

    for col in (TYPE_APPLIED, TYPE_THESIS):
        if col not in pivot_agreement.columns:
            pivot_agreement[col] = 0.0
        if col not in pivot_payment.columns:
            pivot_payment[col] = 0.0

    pivot_agreement = pivot_agreement.reset_index()
    pivot_payment = pivot_payment.reset_index()

    merged = pivot_agreement.merge(
        pivot_payment,
        on=["employer_code", "employer_name", "university_id", "university_name"],
        suffixes=("_agr", "_pay"),
    )

    table_df = pd.DataFrame({
        COL_CODE: merged["employer_code"],
        COL_EMPLOYER: merged["employer_name"],
        COL_UNIVERSITY: merged["university_name"],
        COL_AGR_APPLIED: merged[f"{TYPE_APPLIED}_agr"],
        COL_AGR_THESIS: merged[f"{TYPE_THESIS}_agr"],
        COL_AGR_TOTAL: merged[f"{TYPE_APPLIED}_agr"] + merged[f"{TYPE_THESIS}_agr"],
        COL_PAY_APPLIED: merged[f"{TYPE_APPLIED}_pay"],
        COL_PAY_THESIS: merged[f"{TYPE_THESIS}_pay"],
        COL_PAY_TOTAL: merged[f"{TYPE_APPLIED}_pay"] + merged[f"{TYPE_THESIS}_pay"],
    }).sort_values([COL_EMPLOYER, COL_UNIVERSITY])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        table_df.to_excel(writer, sheet_name="داده خام جدول ۲", index=False)
        detail_df.to_excel(writer, sheet_name="جزئیات قراردادها", index=False)

    print(f"Generated {OUTPUT_PATH}")
    print(f"Employer-University pairs: {len(table_df)}")
    print(f"Distinct contracts: {contracts.shape[0]} "
          f"({(contracts['project_type'] == TYPE_APPLIED).sum()} کاربردی / "
          f"{(contracts['project_type'] == TYPE_THESIS).sum()} رساله)")
    print(f"Total agreement amount: {table_df[COL_AGR_TOTAL].sum():,.0f} Rials")
    print(f"Total payment amount:   {table_df[COL_PAY_TOTAL].sum():,.0f} Rials")


if __name__ == "__main__":
    main()
