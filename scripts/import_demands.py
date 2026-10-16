"""Import demands ("تقاضاها") from a full registry export (All_Demands.xlsx).

Idempotent: existing ``tracking_code``s are skipped, so re-running after
adding new rows to the source file only imports the new ones.

Usage: python scripts/import_demands.py [path/to/All_Demands.xlsx]
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import Base, SessionLocal, engine
from core.date_helper import parse_strict_jalali_date
from models.demand import Demand
from models.employer import Employer

DEFAULT_EXCEL_PATH = Path(__file__).resolve().parents[1] / "results" / "sate_perf" / "data" / "All_Demands.xlsx"

COLUMN_MAP = {
    "کد رهگیری": "tracking_code",
    "متقاضی": "applicant_name",
    "گروه تقاضا": "demand_group",
    "محل تامین اعتبار": "funding_source",
    "ماهیت تقاضا": "demand_nature",
    "حوزه تقاضا": "demand_domain",
    "عنوان تقاضا": "title",
    "نوع تقاضا": "demand_type",
    "تاریخ تقاضا": "demand_date_raw",
}

BATCH_SIZE = 200


def _clean_str(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _parse_demand_date(value):
    text = _clean_str(value)
    if not text:
        return None
    try:
        return parse_strict_jalali_date(text)
    except (TypeError, ValueError) as exc:
        print(f"  [WARNING] Invalid demand date '{text}': {exc}")
        return None


def import_demands(excel_path: Path = DEFAULT_EXCEL_PATH) -> None:
    Base.metadata.create_all(bind=engine, tables=[Demand.__table__])

    print(f"Reading: {excel_path}")
    df = pd.read_excel(excel_path)
    df = df.rename(columns=COLUMN_MAP)
    print(f"[OK] Loaded {len(df)} rows")

    db = SessionLocal()
    try:
        employer_name_to_code = {
            e.name.strip(): e.classification_code
            for e in db.query(Employer).filter(Employer.is_deleted == False).all()  # noqa: E712
        }
        existing_codes = {
            code for (code,) in db.query(Demand.tracking_code).all()
        }
        print(f"[OK] {len(existing_codes)} demands already in database (will be skipped)")

        added = 0
        skipped_duplicate = 0
        skipped_invalid = 0
        matched_employer = 0

        for _, row in df.iterrows():
            tracking_code_raw = row.get("tracking_code")
            if pd.isna(tracking_code_raw):
                skipped_invalid += 1
                continue
            tracking_code = str(int(tracking_code_raw))

            if tracking_code in existing_codes:
                skipped_duplicate += 1
                continue

            applicant_name = _clean_str(row.get("applicant_name"))
            title = _clean_str(row.get("title"))
            if not applicant_name or not title:
                skipped_invalid += 1
                continue

            employer_code = employer_name_to_code.get(applicant_name)
            if employer_code:
                matched_employer += 1

            demand = Demand(
                tracking_code=tracking_code,
                applicant_name=applicant_name,
                employer_code=employer_code,
                demand_group=_clean_str(row.get("demand_group")),
                funding_source=_clean_str(row.get("funding_source")),
                demand_nature=_clean_str(row.get("demand_nature")),
                demand_domain=_clean_str(row.get("demand_domain")),
                title=title,
                demand_type=_clean_str(row.get("demand_type")),
                demand_date=_parse_demand_date(row.get("demand_date_raw")),
            )
            db.add(demand)
            existing_codes.add(tracking_code)
            added += 1

            if added % BATCH_SIZE == 0:
                db.commit()
                print(f"  Progress: {added} demands added")

        db.commit()

        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"[OK] Imported: {added} demands")
        print(f"[OK] Resolved to an existing employer_code: {matched_employer}/{added}")
        print(f"[SKIP] Already in database: {skipped_duplicate}")
        print(f"[SKIP] Missing tracking_code/applicant/title: {skipped_invalid}")
        print(f"Total rows in source file: {len(df)}")
        print("=" * 60)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_EXCEL_PATH
    import_demands(path)
