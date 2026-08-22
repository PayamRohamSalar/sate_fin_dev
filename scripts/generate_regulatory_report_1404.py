"""Generate the regulatory-letter response table: payments made by the ATF
Fund (صندوق عتف) in payment_year = 1404 (Jalali), broken down by employer,
executing university, and contract/project.

Context
-------
This report answers the first two (near-identical) sections of a letter
from a regulatory/oversight body reviewing SATE's performance. Both
sections ask for the same four-column table for fiscal year 1404:

    1. نام شرکت، بانک و مؤسسات انتفاعی وابسته به دولت (کارفرما)
    2. نام دانشگاه/مؤسسه آموزش عالی و پژوهشی/جهاد دانشگاهی/پارک علم و فناوری
    3. عنوان طرح
    4. مبلغ پرداختی توسط صندوق عتف

Scope decisions (documented here so they're auditable, not silent):

  * Filtered on ``Payment.payment_year == 1404`` (سال پرداخت / cash-flow
    year), NOT ``funding_year`` (budget-source year) — the letter explicitly
    asks for the "سال پرداخت" column, per the user's instruction.
  * Only rows from the ``payments`` table are included. ``trustee_payments``
    are deliberately EXCLUDED: per Docs/SATE_Living_Documentation.md (§5,
    2026-08-11 entries), those are disbursements the executing institution
    funded directly from its own resources, outside the employer-managed /
    ATF-disbursed budget pool — so they were not "paid by the ATF Fund"
    (صندوق عتف) and do not belong in this table.
  * Granularity is one row per PAYMENT record (not aggregated per
    contract) — a contract that received multiple disbursements in 1404
    appears on multiple rows, each with its own amount. This matches the
    literal reading of "مبلغ پرداختی" as a per-disbursement amount and
    preserves full traceability. If a single summed row per contract is
    preferred instead, set AGGREGATE_BY_CONTRACT = True below and re-run.
  * Only active (``is_deleted == False``) payments/contracts/employers/
    universities are included, per the project's standing soft-delete rule.
  * Amounts are exported as raw numeric base-Rial values (the DB's native
    unit) — no unit conversion is applied.

Output: results/regulatory_report_table1_1404.xlsx
  - Sheet "جدول ۱ - ۱۴۰۴": exactly the 4 columns required by the letter.
  - Sheet "جزئیات و ردیابی": the same rows plus tracking codes/dates, for
    the project team's own internal traceability (not part of the letter's
    required table, kept separate so Sheet 1 can be copied as-is).
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
AGGREGATE_BY_CONTRACT = True

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / f"regulatory_report_table1_{PAYMENT_YEAR}.xlsx"

COL_EMPLOYER = "نام شرکت، بانک و مؤسسات انتفاعی وابسته به دولت (کارفرما)"
COL_UNIVERSITY = "نام دانشگاه/مؤسسه آموزش عالی و پژوهشی/جهاد دانشگاهی/پارک علم و فناوری"
COL_TITLE = "عنوان طرح"
COL_AMOUNT = "مبلغ پرداختی توسط صندوق عتف (ریال)"


def fetch_rows(db) -> pd.DataFrame:
    """Query payments (funded by the ATF pool only) made in PAYMENT_YEAR."""
    query = (
        select(
            Employer.classification_code.label("employer_code"),
            Employer.name.label("employer_name"),
            University.national_id.label("university_id"),
            University.name.label("university_name"),
            Contract.tracking_code.label("contract_tracking_code"),
            Contract.title.label("contract_title"),
            Payment.tracking_code.label("payment_tracking_code"),
            Payment.amount.label("payment_amount"),
            Payment.payment_date.label("payment_date"),
            Payment.funding_year.label("funding_year"),
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
        .order_by(Employer.name, University.name, Contract.tracking_code, Payment.tracking_code)
    )
    rows = db.execute(query).all()
    return pd.DataFrame(rows, columns=[
        "employer_code", "employer_name", "university_id", "university_name",
        "contract_tracking_code", "contract_title", "payment_tracking_code",
        "payment_amount", "payment_date", "funding_year",
    ])


def main() -> None:
    db = SessionLocal()
    try:
        df = fetch_rows(db)
    finally:
        db.close()

    if AGGREGATE_BY_CONTRACT:
        df = (
            df.groupby(
                ["employer_name", "university_name", "contract_tracking_code", "contract_title"],
                as_index=False,
            )["payment_amount"].sum()
        )

    table_df = pd.DataFrame({
        COL_EMPLOYER: df["employer_name"],
        COL_UNIVERSITY: df["university_name"],
        COL_TITLE: df["contract_title"],
        COL_AMOUNT: df["payment_amount"],
    })

    detail_df = df.rename(columns={
        "employer_code": "کد کارفرما",
        "employer_name": "نام کارفرما",
        "university_id": "شناسه دانشگاه",
        "university_name": "نام دانشگاه",
        "contract_tracking_code": "کد رهگیری قرارداد",
        "contract_title": "عنوان طرح",
        "payment_tracking_code": "کد رهگیری پرداخت",
        "payment_amount": "مبلغ پرداختی (ریال)",
        "payment_date": "تاریخ پرداخت (میلادی)",
        "funding_year": "سال تأمین اعتبار",
    })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        table_df.to_excel(writer, sheet_name=f"جدول ۱ - {PAYMENT_YEAR}", index=False)
        if not AGGREGATE_BY_CONTRACT:
            detail_df.to_excel(writer, sheet_name="جزئیات و ردیابی", index=False)

    print(f"Generated {OUTPUT_PATH}")
    print(f"Rows in table: {len(table_df)}")
    print(f"Distinct employers: {df['employer_name'].nunique()}")
    print(f"Distinct universities: {df['university_name'].nunique()}")
    print(f"Distinct contracts: {df['contract_tracking_code'].nunique()}")
    print(f"Total amount (Rials): {df['payment_amount'].sum():,.0f}")


if __name__ == "__main__":
    main()
