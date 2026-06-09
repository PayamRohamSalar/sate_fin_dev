import os
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Budget.xlsx"
PROCESSED_MANDATES_PATH = PROJECT_ROOT / "data" / "processed_mandates.csv"
PROCESSED_RECEIPTS_PATH = PROJECT_ROOT / "data" / "processed_receipts.csv"

EMPLOYER_CODE_COLUMN = "شماره طبقه بندی"
ASSIGNED_SHEET = "Assigned_Budgets"
DEPOSIT_SHEET = "Deposit_Budget"


def normalize_code(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if not value:
        return None
    if value.endswith(".0"):
        value = value[:-2]
    return value


def clean_amount(value):
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value:
            return 0
    return pd.to_numeric(value, errors="coerce")


def extract_year(column_name):
    match = re.search(r"(\d{4})", str(column_name))
    if not match:
        raise ValueError(f"Could not extract fiscal year from column: {column_name}")
    return int(match.group(1))


def melt_budget_sheet(
    df: pd.DataFrame,
    value_name: str,
    expected_prefix: str,
) -> pd.DataFrame:
    if EMPLOYER_CODE_COLUMN not in df.columns:
        raise ValueError(f"Missing required column: {EMPLOYER_CODE_COLUMN}")

    value_columns = [
        column
        for column in df.columns
        if column != EMPLOYER_CODE_COLUMN and str(column).strip().startswith(expected_prefix)
    ]
    if not value_columns:
        raise ValueError(f"No budget columns found with prefix: {expected_prefix}")

    melted = pd.melt(
        df,
        id_vars=[EMPLOYER_CODE_COLUMN],
        value_vars=value_columns,
        var_name="fiscal_year",
        value_name=value_name,
    )
    melted = melted.rename(columns={EMPLOYER_CODE_COLUMN: "employer_code"})
    melted["employer_code"] = melted["employer_code"].apply(normalize_code)
    melted["fiscal_year"] = melted["fiscal_year"].apply(extract_year)
    melted[value_name] = melted[value_name].apply(clean_amount).fillna(0)
    melted = melted.dropna(subset=["employer_code"])
    return melted


def process_budgets(file_path: Path = EXCEL_FILE_PATH) -> None:
    assigned_df = pd.read_excel(
        file_path,
        sheet_name=ASSIGNED_SHEET,
        engine="openpyxl",
        dtype={EMPLOYER_CODE_COLUMN: str},
    )
    deposit_df = pd.read_excel(
        file_path,
        sheet_name=DEPOSIT_SHEET,
        engine="openpyxl",
        dtype={EMPLOYER_CODE_COLUMN: str},
    )

    assigned_long = melt_budget_sheet(
        assigned_df,
        value_name="mandated_amount",
        expected_prefix="سال",
    )
    deposit_long = melt_budget_sheet(
        deposit_df,
        value_name="deposited_amount",
        expected_prefix="واریزی",
    )

    assigned_long["has_assigned_budget"] = True
    merged = pd.merge(
        assigned_long,
        deposit_long,
        on=["employer_code", "fiscal_year"],
        how="outer",
    )
    merged["mandated_amount"] = merged["mandated_amount"].fillna(0)
    merged["deposited_amount"] = merged["deposited_amount"].fillna(0)
    merged["has_assigned_budget"] = merged["has_assigned_budget"].fillna(False)

    mandates = merged.loc[
        merged["has_assigned_budget"],
        ["employer_code", "fiscal_year", "mandated_amount"],
    ].copy()
    mandates = mandates.sort_values(["employer_code", "fiscal_year"])

    receipts = merged.loc[
        merged["deposited_amount"] > 0,
        ["employer_code", "fiscal_year", "deposited_amount"],
    ].copy()
    receipts["deposit_date"] = receipts["fiscal_year"].astype(int).astype(str) + "-12-29"
    receipts["description"] = "Historical Aggregated Deposit"
    receipts = receipts.sort_values(["employer_code", "fiscal_year"])

    mandates.to_csv(PROCESSED_MANDATES_PATH, index=False, encoding="utf-8-sig")
    receipts.to_csv(PROCESSED_RECEIPTS_PATH, index=False, encoding="utf-8-sig")

    print(f"Exported {len(mandates)} mandates to {PROCESSED_MANDATES_PATH}")
    print(f"Exported {len(receipts)} receipts to {PROCESSED_RECEIPTS_PATH}")


if __name__ == "__main__":
    process_budgets()
