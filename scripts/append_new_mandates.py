import os
import sys
from pathlib import Path

import pandas as pd

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "New_Mandates.xlsx"

# Unit conversion: Excel values are in Billion Rials, convert to base Rials
BILLION = 1_000_000_000

# Target fiscal year for the new mandates
TARGET_FISCAL_YEAR = 1406


def normalize_code(value):
    """Normalize employer code by removing .0 suffix from numeric strings."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        return value[:-2]
    return value


def append_new_mandates(file_path: Path = EXCEL_FILE_PATH, fiscal_year: int = TARGET_FISCAL_YEAR):
    """Append new mandate records to the annual_mandates table without dropping existing data."""
    
    print(f"=== Append New Mandates for Fiscal Year {fiscal_year} ===")
    print(f"Reading Excel file: {file_path}")
    
    # Read the Excel file
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"Loaded {len(df)} rows from Excel")
    print(f"Columns: {list(df.columns)}")
    
    # Validate required columns
    required_cols = ['شماره طبقه بندی', 'اعتبار تکلیفی']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Normalize and prepare data
    df['employer_code'] = df['شماره طبقه بندی'].apply(normalize_code)
    df['mandated_amount'] = pd.to_numeric(df['اعتبار تکلیفی'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    df['mandated_amount'] = df['mandated_amount'] * BILLION
    
    print(f"Converted amounts to base Rials (×{BILLION:,})")
    
    # Start database transaction
    db = SessionLocal()
    try:
        # Get valid employer codes from database
        valid_codes = {emp.classification_code for emp in db.query(Employer.classification_code).all()}
        print(f"Found {len(valid_codes)} valid employer codes in database")
        
        # Get existing mandates for this fiscal year
        existing_mandates = {
            (m.employer_code, m.fiscal_year) 
            for m in db.query(AnnualMandate.employer_code, AnnualMandate.fiscal_year)
                      .filter(AnnualMandate.fiscal_year == fiscal_year)
                      .all()
        }
        print(f"Found {len(existing_mandates)} existing mandates for fiscal year {fiscal_year}")
        
        # Process each row
        added = 0
        updated = 0
        skipped_missing_employer = 0
        skipped_duplicate = 0
        
        for idx, row in df.iterrows():
            employer_code = row['employer_code']
            mandated_amount = float(row['mandated_amount'])
            
            # Validation 1: Check if employer exists
            if employer_code not in valid_codes:
                print(f"WARNING: Row {idx} - employer_code '{employer_code}' not found in database. Skipping.")
                skipped_missing_employer += 1
                continue
            
            # Validation 2: Check for existing mandate
            if (employer_code, fiscal_year) in existing_mandates:
                # Update existing record instead of creating duplicate
                existing_mandate = db.query(AnnualMandate).filter_by(
                    employer_code=employer_code,
                    fiscal_year=fiscal_year
                ).first()
                
                if existing_mandate:
                    old_amount = existing_mandate.mandated_amount
                    existing_mandate.mandated_amount = mandated_amount
                    updated += 1
                    print(f"Updated: {employer_code} - Year {fiscal_year}: {old_amount:,.2f} → {mandated_amount:,.2f} Rials")
                continue
            
            # Insert new mandate
            new_mandate = AnnualMandate(
                employer_code=employer_code,
                fiscal_year=fiscal_year,
                mandated_amount=mandated_amount
            )
            db.add(new_mandate)
            added += 1
        
        # Commit transaction
        db.commit()
        
        print("\n=== Import Summary ===")
        print(f"✓ Successfully added {added} new Annual_Mandate records")
        print(f"✓ Successfully updated {updated} existing Annual_Mandate records")
        print(f"⚠ Skipped {skipped_missing_employer} rows due to missing employer codes")
        print(f"ℹ Skipped {skipped_duplicate} rows due to existing mandates (already handled via update)")
        print(f"\nNote: All monetary values converted from Billion Rials to base Rials (×{BILLION:,})")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Database transaction failed. Rolled back.")
        print(f"Error details: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    append_new_mandates()
