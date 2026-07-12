"""Generate an Excel breakdown of dynamically calculated contract statuses."""

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from services.financial_engine import get_contracts_with_dynamic_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / "contract_status_breakdown.xlsx"
STATUS_ORDER = ["Completed", "Stagnant", "Active"]
STATUS_TRANSLATIONS = {
    "Completed": "خاتمه‌یافته",
    "Stagnant": "راکد",
    "Active": "فعال",
}
DETAIL_COLUMN_TRANSLATIONS = {
    "tracking_code": "کد رهگیری",
    "employer_code": "کد دستگاه",
    "university_id": "شناسه دانشگاه",
    "researcher_id": "کد ملی پژوهشگر",
    "proposal_id": "شناسه پیشنهاد",
    "contract_number": "شماره قرارداد",
    "contract_date": "تاریخ قرارداد",
    "contract_creation_year": "سال انعقاد (شمسی)",
    "total_amount": "مبلغ کل قرارداد (ریال)",
    "total_paid": "مجموع پرداختی (ریال)",
    "last_payment_funding_year": "سال تأمین اعتبار آخرین پرداخت",
    "activity_year": "سال آخرین فعالیت",
    "dynamic_status": "وضعیت قرارداد",
    "title": "عنوان قرارداد",
}
SUMMARY_COLUMN_TRANSLATIONS = {
    "contract_creation_year": "سال انعقاد (شمسی)",
    "Completed": "خاتمه‌یافته",
    "Stagnant": "راکد",
    "Active": "فعال",
    "Total": "مجموع",
}


def _results_to_dataframe(rows) -> pd.DataFrame:
    """Convert SQLAlchemy result rows into report-friendly contract records."""
    records = []
    for row in rows:
        contract = row.Contract
        records.append(
            {
                "tracking_code": contract.tracking_code,
                "employer_code": contract.employer_code,
                "university_id": contract.university_id,
                "researcher_id": contract.researcher_id,
                "proposal_id": contract.proposal_id,
                "contract_number": contract.contract_number,
                "contract_date": contract.contract_date,
                "contract_creation_year": int(row.contract_creation_year) if row.contract_creation_year is not None else None,
                "total_amount": contract.total_amount,
                "total_paid": row.total_paid,
                "last_payment_funding_year": row.last_payment_funding_year,
                "activity_year": int(row.activity_year) if row.activity_year is not None else None,
                "dynamic_status": row.dynamic_status,
                "title": contract.title,
            }
        )
    return pd.DataFrame(records)


def _build_summary(details: pd.DataFrame) -> pd.DataFrame:
    """Aggregate contract counts by Jalali creation year and dynamic status."""
    if details.empty:
        return pd.DataFrame(columns=["contract_creation_year", *STATUS_ORDER, "Total"])

    summary = pd.pivot_table(
        details,
        index="contract_creation_year",
        columns="dynamic_status",
        values="tracking_code",
        aggfunc="count",
        fill_value=0,
    )
    summary = summary.reindex(columns=STATUS_ORDER, fill_value=0)
    summary["Total"] = summary.sum(axis=1)
    return summary.reset_index().sort_values("contract_creation_year", na_position="last")


def main() -> None:
    """Generate detailed and aggregated contract status Excel worksheets."""
    db = SessionLocal()
    try:
        rows = get_contracts_with_dynamic_status(db, threshold_year=1402)
        details = _results_to_dataframe(rows)
        summary = _build_summary(details)

        if "dynamic_status" in details.columns:
            details["dynamic_status"] = details["dynamic_status"].replace(
                STATUS_TRANSLATIONS
            )
        details = details.rename(columns=DETAIL_COLUMN_TRANSLATIONS)
        summary = summary.rename(columns=SUMMARY_COLUMN_TRANSLATIONS)

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="Summary Dashboard", index=False)
            details.to_excel(writer, sheet_name="Detailed Data", index=False)

        print(f"Generated {OUTPUT_PATH}")
        print(f"Detailed contracts: {len(details)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
