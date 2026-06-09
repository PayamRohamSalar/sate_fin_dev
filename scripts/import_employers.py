import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.employer import Employer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Employers.xlsx"

COLUMN_MAPPING = {
    "شماره طبقه بندی": "classification_code",
    "نام مشمول": "name",
    "نوع مشمول": "employer_type",
    "شماره طبقه بندی سازمان مادر": "parent_code",
    "استان": "province",
    "عنوان امور": "affairs_category",
    "دستگاه اجرایی بالادست": "upper_organization",
    "وضعیت فعالیت": "status",
}

EMPLOYER_TYPE_MAPPING = {
    "مادر": "Mother",
    "زیرمجموعه": "Subsidiary",
    "مستقل": "Independent",
}

STATUS_MAPPING = {
    "فعال": "Active",
    "غیرفعال": "Inactive",
}

UNKNOWN_REQUIRED_VALUE = "Unknown"


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value).strip()


def normalize_code(value):
    value = clean_value(value)
    if value is None:
        return None
    if value.endswith(".0"):
        return value[:-2]
    return value


def normalize_employer_type(value):
    value = clean_value(value)
    return EMPLOYER_TYPE_MAPPING.get(value, value)


def normalize_status(value):
    value = clean_value(value)
    if value is None:
        return "Active"
    return STATUS_MAPPING.get(value, value)


def load_employers_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing Excel columns: {sorted(missing_columns)}")
    df = df.rename(columns=COLUMN_MAPPING)
    return df.where(pd.notnull(df), None)


def build_employer(row) -> Employer:
    classification_code = normalize_code(row["classification_code"])
    if classification_code is None:
        raise ValueError("classification_code is required")

    return Employer(
        classification_code=classification_code,
        name=clean_value(row["name"]) or UNKNOWN_REQUIRED_VALUE,
        employer_type=normalize_employer_type(row["employer_type"]),
        parent_code=normalize_code(row["parent_code"]),
        province=clean_value(row["province"]) or UNKNOWN_REQUIRED_VALUE,
        affairs_category=clean_value(row["affairs_category"]),
        upper_organization=clean_value(row["upper_organization"]) or UNKNOWN_REQUIRED_VALUE,
        status=normalize_status(row["status"]),
    )


def import_employers(file_path: Path = EXCEL_FILE_PATH) -> None:
    Employer.__table__.drop(engine, checkfirst=True)
    Base.metadata.create_all(bind=engine)

    print(f"Reading Excel file: {file_path}")
    df = load_employers_dataframe(file_path)
    print(f"Loaded {len(df)} rows from Excel.")

    db = SessionLocal()
    records_added = 0
    duplicates_skipped = 0

    try:
        for index, row in df.iterrows():
            employer = build_employer(row)

            existing_employer = (
                db.query(Employer)
                .filter_by(classification_code=employer.classification_code)
                .first()
            )
            if existing_employer:
                duplicates_skipped += 1
                print(f"Skipping duplicate: {employer.classification_code}")
                continue

            db.add(employer)
            records_added += 1

        db.commit()
        print("Import committed successfully.")
        print(f"Successfully imported {records_added} new employers.")
        print(f"Skipped {duplicates_skipped} existing employers.")
    except Exception:
        db.rollback()
        print("Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_employers()
