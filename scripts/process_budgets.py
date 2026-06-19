import re
import pandas as pd
from pathlib import Path

# ==========================================
# Configuration and Constants
# ==========================================
# Defining absolute paths using pathlib for Windows compatibility
BASE_DIR = Path(r"C:\Users\pchin\OneDrive\AI-Project\SATE_Fin_Dev\data")
INPUT_EXCEL_FILE = BASE_DIR / "Budget.xlsx"
OUTPUT_EXCEL_FILE = BASE_DIR / "Budget_longformat.xlsx"

ASSIGNED_SHEET_NAME = "Assigned_Budgets"
DEPOSIT_SHEET_NAME = "Deposit_Budget"
EMPLOYER_CODE_COL = "شماره طبقه بندی"

def clean_employer_code(value: str) -> str:
    """
    Normalizes the employer code by stripping whitespaces and removing trailing '.0'.
    Returns None if the value is invalid or empty.
    """
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def clean_financial_amount(value: str) -> float:
    """
    Cleans financial amount strings (removes commas, handles empty strings) 
    and converts them to float. Prevents calculation errors by returning 0.0 for blanks.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value:
            return 0.0
    return pd.to_numeric(value, errors="coerce")

def extract_fiscal_year(column_name: str) -> int:
    """
    Extracts the 4-digit fiscal year from a given column header.
    Raises ValueError if no year is found, preventing silent data corruption.
    """
    match = re.search(r"(\d{4})", str(column_name))
    if not match:
        raise ValueError(f"CRITICAL: Could not extract fiscal year from: {column_name}")
    return int(match.group(1))

def process_budget_data() -> None:
    """
    Main ETL pipeline: Reads multi-sheet Excel safely, melts data to long format,
    applies business logic, and exports to the exact target directory.
    """
    # 1. Validate Directory Existence
    if not BASE_DIR.exists():
        print(f"Error: The directory {BASE_DIR} does not exist.")
        return

    # 2. Read Excel File using ExcelFile for atomic loading and performance
    print(f"Loading data from: {INPUT_EXCEL_FILE}")
    try:
        with pd.ExcelFile(INPUT_EXCEL_FILE) as xls:
            df_assigned_wide = pd.read_excel(xls, sheet_name=ASSIGNED_SHEET_NAME)
            df_deposit_wide = pd.read_excel(xls, sheet_name=DEPOSIT_SHEET_NAME)
    except FileNotFoundError:
        print(f"Error: The file {INPUT_EXCEL_FILE} was not found.")
        return
    except ValueError as e:
        print(f"Error reading sheets: {e}")
        return

    # 3. Process Assigned Budgets (Mandates)
    print("Processing Assigned Budgets...")
    df_assigned_long = pd.melt(
        df_assigned_wide,
        id_vars=[EMPLOYER_CODE_COL],
        var_name="Year_Raw",
        value_name="Assigned_Amount"
    )
    df_assigned_long["Fiscal_Year"] = df_assigned_long["Year_Raw"].apply(extract_fiscal_year)
    df_assigned_long[EMPLOYER_CODE_COL] = df_assigned_long[EMPLOYER_CODE_COL].apply(clean_employer_code)
    #df_assigned_long["Assigned_Amount"] = df_assigned_long["Assigned_Amount"].apply(clean_financial_amount)
    df_assigned_long["Assigned_Amount"] = df_assigned_long["Assigned_Amount"].apply(clean_financial_amount) * 1_000_000_000
    
    # Implementing Soft Delete mechanism for database mapping
    df_assigned_long["Is_Deleted"] = False
    df_assigned_long.drop(columns=["Year_Raw"], inplace=True)

    # 4. Process Deposit Budgets
    print("Processing Deposit Budgets...")
    df_deposit_long = pd.melt(
        df_deposit_wide,
        id_vars=[EMPLOYER_CODE_COL],
        var_name="Year_Raw",
        value_name="Deposit_Amount"
    )
    df_deposit_long["Fiscal_Year"] = df_deposit_long["Year_Raw"].apply(extract_fiscal_year)
    df_deposit_long[EMPLOYER_CODE_COL] = df_deposit_long[EMPLOYER_CODE_COL].apply(clean_employer_code)
    df_deposit_long["Deposit_Amount"] = df_deposit_long["Deposit_Amount"].apply(clean_financial_amount)
    
    # Implementing Soft Delete mechanism
    df_deposit_long["Is_Deleted"] = False
    df_deposit_long.drop(columns=["Year_Raw"], inplace=True)

    # 5. Merge Data securely to prevent data loss (Outer Join)
    print("Merging data...")
    df_merged = pd.merge(
        df_assigned_long,
        df_deposit_long,
        on=[EMPLOYER_CODE_COL, "Fiscal_Year"],
        how="outer",
        suffixes=("_assigned", "_deposit")
    )
    
    # Resolving data nulls after outer merge to maintain mathematical accuracy
    df_merged["Is_Deleted"] = False 
    df_merged["Assigned_Amount"] = df_merged["Assigned_Amount"].fillna(0.0)
    df_merged["Deposit_Amount"] = df_merged["Deposit_Amount"].fillna(0.0)
    
    # Clean up: Remove rows where there is absolutely no financial activity
    df_merged = df_merged[(df_merged["Assigned_Amount"] > 0) | (df_merged["Deposit_Amount"] > 0)]

    # 6. Export to Excel in target directory
    print(f"Exporting processed data to: {OUTPUT_EXCEL_FILE}")
    with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine='xlsxwriter') as writer:
        df_merged.to_excel(writer, sheet_name='Merged_Master_Data', index=False)
        df_assigned_long.to_excel(writer, sheet_name='Assigned_LongFormat', index=False)
        df_deposit_long.to_excel(writer, sheet_name='Deposit_LongFormat', index=False)
    
    print("Data processing complete. Data integrity maintained.")

if __name__ == "__main__":
    process_budget_data()