"""
Financial Report Generator
Exports employer balances using the centralized macro engine in financial_engine.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from services.financial_engine import get_all_employers_financials

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / "financial_report_summary.xlsx"

PERSIAN_COLUMNS = [
    "کد مشمول",
    "نام مشمول",
    "سال مالی",
    "اعتبار تکلیفی (ریال)",
    "مجموع واریزی (ریال)",
    "هزینه کرد (ریال)",
    "انتقال ورودی (ریال)",
    "انتقال خروجی (ریال)",
    "مانده واقعی (ریال)",
]

COLUMN_MAPPING = {
    "employer_code": PERSIAN_COLUMNS[0],
    "employer_name": PERSIAN_COLUMNS[1],
    "year": PERSIAN_COLUMNS[2],
    "mandated_amount": PERSIAN_COLUMNS[3],
    "deposit_amount": PERSIAN_COLUMNS[4],
    "payment_amount": PERSIAN_COLUMNS[5],
    "transfer_in": PERSIAN_COLUMNS[6],
    "transfer_out": PERSIAN_COLUMNS[7],
    "balance": PERSIAN_COLUMNS[8],
}


def main():
    print("=" * 60)
    print("Financial Report Generator - Employer Balance Analysis")
    print("=" * 60)

    db = SessionLocal()
    try:
        print("\n[1/3] Calculating employer financials via macro engine...")
        df = get_all_employers_financials(db)

        if df.empty:
            print("   No financial data found.")
            return

        print(f"   Loaded {df['employer_code'].nunique()} employers")
        print(f"   Generated {len(df)} employer-year records")

        print("\n[2/3] Formatting report columns...")
        df_report = df.rename(columns=COLUMN_MAPPING)
        df_report = df_report.sort_values([PERSIAN_COLUMNS[0], PERSIAN_COLUMNS[2]])

        print("\n[3/3] Exporting to Excel...")
        OUTPUT_PATH.parent.mkdir(exist_ok=True)
        df_report.to_excel(OUTPUT_PATH, index=False, engine="openpyxl")
        print(f"   Exported to: {OUTPUT_PATH}")

        print("\n" + "=" * 60)
        print("REPORT SUMMARY")
        print("=" * 60)
        print(f"Total employers:        {df_report[PERSIAN_COLUMNS[0]].nunique()}")
        print(f"Total fiscal years:     {df_report[PERSIAN_COLUMNS[2]].nunique()}")
        print(
            f"Total mandated amount:  "
            f"{df_report[PERSIAN_COLUMNS[3]].sum():,.0f} Rials"
        )
        print(
            f"Total deposited:        "
            f"{df_report[PERSIAN_COLUMNS[4]].sum():,.0f} Rials"
        )
        print(
            f"Total payments:         "
            f"{df_report[PERSIAN_COLUMNS[5]].sum():,.0f} Rials"
        )
        print(
            f"Total transfers in:     "
            f"{df_report[PERSIAN_COLUMNS[6]].sum():,.0f} Rials"
        )
        print(
            f"Total transfers out:    "
            f"{df_report[PERSIAN_COLUMNS[7]].sum():,.0f} Rials"
        )
        print(
            f"Total real balance:     "
            f"{df_report[PERSIAN_COLUMNS[8]].sum():,.0f} Rials"
        )
        print("=" * 60)
        print("\nFinancial report generation completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
