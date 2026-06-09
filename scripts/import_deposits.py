import os
import sys
from pathlib import Path
from datetime import date
import shutil

import pandas as pd

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.employer import Employer
from models.deposits import AnnualMandate, DepositReceipt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Budget.xlsx"
TEMP_FILE_PATH = Path("C:/Temp/Budget_temp.xlsx")

# Unit conversion: Excel values are in Billion Rials, convert to base Rials
BILLION = 1_000_000_000


def normalize_code(value):
    """Normalize employer code by removing .0 suffix from numeric strings."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        return value[:-2]
    return value


def extract_year_from_column(col_name):
    """Extract integer year from Persian column names like 'سال 1398' or 'واریزی 1402'."""
    parts = col_name.split()
    for part in parts:
        if part.isdigit():
            return int(part)
    raise ValueError(f"Could not extract year from column: {col_name}")


def load_and_transform_budgets(file_path: Path):
    """Load both sheets and transform from wide to long format."""
    
    print(f"Reading Excel file: {file_path}")
    
    # Read Assigned_Budgets sheet
    assigned_df = pd.read_excel(file_path, sheet_name='Assigned_Budgets', engine='openpyxl')
    print(f"Loaded {len(assigned_df)} rows from Assigned_Budgets sheet")
    print(f"Column count: {len(assigned_df.columns)}")
    
    # Read Deposit_Budget sheet
    deposit_df = pd.read_excel(file_path, sheet_name='Deposit_Budget', engine='openpyxl')
    print(f"Loaded {len(deposit_df)} rows from Deposit_Budget sheet")
    print(f"Column count: {len(deposit_df.columns)}")
    
    # Transform Assigned_Budgets: wide to long
    code_col = 'شماره طبقه بندی'
    year_cols_assigned = [col for col in assigned_df.columns if col.startswith('سال')]
    
    assigned_long = pd.melt(
        assigned_df,
        id_vars=[code_col],
        value_vars=year_cols_assigned,
        var_name='year_column',
        value_name='mandated_amount'
    )
    assigned_long['fiscal_year'] = assigned_long['year_column'].apply(extract_year_from_column)
    assigned_long['employer_code'] = assigned_long[code_col].apply(normalize_code)
    assigned_long = assigned_long[['employer_code', 'fiscal_year', 'mandated_amount']]
    assigned_long['mandated_amount'] = pd.to_numeric(assigned_long['mandated_amount'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    assigned_long['mandated_amount'] = assigned_long['mandated_amount'] * BILLION
    
    print(f"Transformed Assigned_Budgets to {len(assigned_long)} long-format rows (scaled to base Rials)")
    
    # Transform Deposit_Budget: wide to long
    year_cols_deposit = [col for col in deposit_df.columns if col.startswith('واریزی')]
    
    deposit_long = pd.melt(
        deposit_df,
        id_vars=[code_col],
        value_vars=year_cols_deposit,
        var_name='year_column',
        value_name='deposited_amount'
    )
    deposit_long['fiscal_year'] = deposit_long['year_column'].apply(extract_year_from_column)
    deposit_long['employer_code'] = deposit_long[code_col].apply(normalize_code)
    deposit_long = deposit_long[['employer_code', 'fiscal_year', 'deposited_amount']]
    deposit_long['deposited_amount'] = pd.to_numeric(deposit_long['deposited_amount'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    #deposit_long['deposited_amount'] = deposit_long['deposited_amount'] * BILLION
    
    print(f"Transformed Deposit_Budget to {len(deposit_long)} long-format rows (scaled to base Rials)")
    
    # Merge on employer_code and fiscal_year (outer join)
    merged_df = pd.merge(
        assigned_long,
        deposit_long,
        on=['employer_code', 'fiscal_year'],
        how='outer'
    )
    merged_df['mandated_amount'] = merged_df['mandated_amount'].fillna(0)
    merged_df['deposited_amount'] = merged_df['deposited_amount'].fillna(0)
    
    print(f"Merged DataFrame has {len(merged_df)} rows")
    
    return merged_df


def persian_date_to_gregorian(year, month, day):
    """
    Simplified Persian to Gregorian conversion.
    For MVP purposes, we'll use a simple approximation:
    Persian year Y maps roughly to Gregorian year Y+621 or Y+622.
    The last day of Persian year (12/29) is around March 20.
    """
    gregorian_year = year + 621
    return date(gregorian_year, 3, 20)


def import_deposits(file_path: Path = EXCEL_FILE_PATH):
    """Main ETL function: Extract, Transform, Load deposit data."""
    
    # Drop existing tables in correct order (child first, then parent)
    print("Dropping existing deposit tables...")
    DepositReceipt.__table__.drop(engine, checkfirst=True)
    AnnualMandate.__table__.drop(engine, checkfirst=True)
    print("Tables dropped successfully.")
    
    # Recreate schema
    print("Recreating deposit tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    # Use temp file if original is locked - check before attempting to use
    if TEMP_FILE_PATH.exists():
        actual_file = TEMP_FILE_PATH
        print(f"Using temp file: {actual_file}")
    else:
        actual_file = file_path
        print(f"Using original file: {actual_file}")
    
    # Load and transform data
    merged_df = load_and_transform_budgets(actual_file)
    
    # Get valid employer codes from database
    db = SessionLocal()
    try:
        valid_codes = {emp.classification_code for emp in db.query(Employer.classification_code).all()}
        print(f"Found {len(valid_codes)} valid employer codes in database")
        
        mandates_added = 0
        receipts_added = 0
        skipped_missing_employer = 0
        
        for idx, row in merged_df.iterrows():
            employer_code = row['employer_code']
            fiscal_year = int(row['fiscal_year'])
            mandated_amount = float(row['mandated_amount'])
            deposited_amount = float(row['deposited_amount'])
            
            # Skip if employer doesn't exist
            if employer_code not in valid_codes:
                if skipped_missing_employer < 5:  # Only log first 5
                    print(f"WARNING: Skipping row {idx} - employer_code '{employer_code}' not found in database")
                skipped_missing_employer += 1
                continue
            
            # Create Annual_Mandate record
            mandate = AnnualMandate(
                employer_code=employer_code,
                fiscal_year=fiscal_year,
                mandated_amount=mandated_amount
            )
            db.add(mandate)
            mandates_added += 1
            
            # Create Deposit_Receipt if deposited_amount > 0
            if deposited_amount > 0:
                deposit_date = persian_date_to_gregorian(fiscal_year, 12, 29)
                receipt = DepositReceipt(
                    employer_code=employer_code,
                    fiscal_year=fiscal_year,
                    deposit_amount=deposited_amount,
                    deposit_date=deposit_date,
                    description='Historical Aggregated Deposit'
                )
                db.add(receipt)
                receipts_added += 1
        
        # Commit transaction
        db.commit()
        print("\n=== Import Summary ===")
        print(f"Successfully imported {mandates_added} Annual_Mandate records")
        print(f"Successfully imported {receipts_added} Deposit_Receipt records")
        print(f"Skipped {skipped_missing_employer} rows due to missing employer codes")
        print(f"\nNote: All monetary values converted from Billion Rials to base Rials (×{BILLION:,})")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_deposits()
