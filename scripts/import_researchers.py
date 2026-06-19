import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.researchers import Researcher
from models.university import University
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Researchers.xlsx"

COLUMN_MAPPING = {
    "کد رهگیری فناور": "tracking_code",
    "کد ملی فناور": "national_code",
    "نام فناور": "first_name",
    "نام خانوادگی فناور": "last_name",
    "تلفن همراه": "mobile",
    "ایمیل": "email",
    "درجه علمی": "academic_rank",
    "شناسه ملی موسسه": "university_id",
    "مدرک تحصیلی": "education_level",
    "نوع فناور": "researcher_type",
    "وضعیت": "status",
}

STATUS_MAPPING = {
    "فعال": "Active",
    "غیرفعال": "Inactive",
}


def clean_value(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value or None


def normalize_status(value):
    value = clean_value(value)
    if value is None:
        return "Active"
    return STATUS_MAPPING.get(value, value)


def load_researchers_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing Excel columns: {sorted(missing_columns)}")
    df = df.rename(columns=COLUMN_MAPPING)
    return df.where(pd.notnull(df), None)


def build_researcher(row) -> Researcher | None:
    national_code = clean_value(row["national_code"])
    if national_code is None:
        return None

    first_name = clean_value(row["first_name"])
    last_name = clean_value(row["last_name"])

    return Researcher(
        national_code=national_code,
        tracking_code=clean_value(row["tracking_code"]),
        first_name=first_name or "Unknown",
        last_name=last_name or "Unknown",
        full_name=f"{first_name or 'Unknown'} {last_name or 'Unknown'}",
        mobile=clean_value(row["mobile"]),
        email=clean_value(row["email"]),
        academic_rank=clean_value(row["academic_rank"]),
        university_id=clean_value(row["university_id"]),
        education_level=clean_value(row["education_level"]),
        researcher_type=clean_value(row["researcher_type"]),
        status=normalize_status(row["status"]),
    )


def import_researchers(file_path: Path = EXCEL_FILE_PATH) -> None:
    # Force drop the table and all its dependents (e.g., contracts)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS researchers CASCADE"))
    Base.metadata.create_all(bind=engine)

    print(f"Reading Excel file: {file_path}")
    df = load_researchers_dataframe(file_path)
    print(f"Loaded {len(df)} rows from Excel.")

    db = SessionLocal()
    records_added = 0
    missing_national_code_skipped = 0
    invalid_university_skipped = 0
    duplicate_skipped = 0
    seen_national_codes = set()

    try:
        valid_universities = {
            national_id for (national_id,) in db.query(University.national_id).all()
        }
        print(f"Loaded {len(valid_universities)} valid universities for FK checks.")

        for index, row in df.iterrows():
            researcher = build_researcher(row)
            if researcher is None:
                missing_national_code_skipped += 1
                continue

            if researcher.national_code in seen_national_codes:
                duplicate_skipped += 1
                print(f"Row {index + 2}: skipping duplicate national_code {researcher.national_code}")
                continue

            if researcher.university_id not in valid_universities:
                invalid_university_skipped += 1
                print(
                    f"Row {index + 2}: skipping researcher {researcher.national_code}; "
                    f"invalid university_id {researcher.university_id}"
                )
                continue

            db.add(researcher)
            seen_national_codes.add(researcher.national_code)
            records_added += 1

        db.commit()
        print("Import committed successfully.")
        print(f"Successfully imported {records_added} researchers.")
        print(f"Skipped {missing_national_code_skipped} rows without national_code.")
        print(f"Skipped {invalid_university_skipped} rows with invalid university_id.")
        print(f"Skipped {duplicate_skipped} duplicate researchers.")
    except Exception:
        db.rollback()
        print("Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_researchers()
