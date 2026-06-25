"""
ETL Script: Import Credit Transfers from Excel
Imports credit transfer data with validation and business logic checks
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from core.database import SessionLocal, engine
from models.transfer import CreditTransfer
from models.contract import Contract
from models.employer import Employer
from services.financial_engine import calculate_real_balance

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "CreditTransfer.xlsx"


def clean_amount(value):
    """Remove commas and convert to numeric"""
    if pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove commas and convert
    cleaned = str(value).replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0


def import_credit_transfers():
    """Main ETL function to import credit transfers"""
    
    print("=" * 70)
    print("Credit Transfer Import Process Started")
    print("=" * 70)
    
    # Statistics counters
    total_rows = 0
    inserted_rows = 0
    skipped_fk_errors = 0
    skipped_insufficient_funds = 0
    
    # Step 1: Drop and recreate table
    print("\n[1/6] Dropping and recreating credit_transfers table...")
    CreditTransfer.__table__.drop(engine, checkfirst=True)
    CreditTransfer.__table__.create(engine, checkfirst=True)
    print("✓ Table recreated successfully")
    
    # Step 2: Read Excel file
    print("\n[2/6] Reading Excel file...")
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        total_rows = len(df)
        print(f"✓ Loaded {total_rows} rows from Excel")
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return
    
    # Step 3: Load validation sets
    print("\n[3/6] Loading validation data...")
    db = SessionLocal()
    try:
        # Load all valid employer codes
        valid_employers = set(
            db.query(Employer.classification_code)
            .filter(Employer.is_deleted == False)
            .all()
        )
        valid_employer_codes = {code[0] for code in valid_employers}
        
        # Load all valid contract tracking codes
        valid_contracts = set(
            db.query(Contract.tracking_code)
            .filter(Contract.is_deleted == False)
            .all()
        )
        valid_contract_codes = {code[0] for code in valid_contracts}
        
        print(f"✓ Loaded {len(valid_employer_codes)} valid employer codes")
        print(f"✓ Loaded {len(valid_contract_codes)} valid contract codes")
        
    except Exception as e:
        print(f"✗ Error loading validation data: {e}")
        db.close()
        return
    
    # Step 4: Column mapping
    print("\n[4/6] Mapping columns...")
    column_mapping = {
        'شماره طبقه بندی شرکت مبدأ': 'source_employer_code',
        'شماره طبقه بندی شرکت مقصد': 'destination_employer_code',
        'کارگزار قرارداد': 'broker_name',
        'انتقال از محل سال مالی': 'fiscal_year',
        'مبلغ انتقال': 'amount',
        'کد رهگیری قرارداد': 'contract_tracking_code'
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    print("✓ Columns mapped successfully")
    
    # Step 5: Process and validate rows
    print("\n[5/6] Processing rows with validation...")
    print("-" * 70)
    
    for idx, row in df.iterrows():
        row_num = idx + 1
        
        # Extract and clean data
        source_code = str(row.get('source_employer_code', '')).strip()
        dest_code = str(row.get('destination_employer_code', '')).strip()
        broker = str(row.get('broker_name', '')).strip() if pd.notna(row.get('broker_name')) else None
        
        try:
            fiscal_year = int(row.get('fiscal_year', 0))
        except (ValueError, TypeError):
            print(f"⚠ Row {row_num}: Invalid fiscal year, skipping")
            skipped_fk_errors += 1
            continue
        
        amount = clean_amount(row.get('amount'))
        contract_code = str(row.get('contract_tracking_code', '')).strip()
        
        # Validation 1: Check foreign key constraints
        if source_code not in valid_employer_codes:
            print(f"⚠ Row {row_num}: Invalid source employer '{source_code}', skipping")
            skipped_fk_errors += 1
            continue
        
        if dest_code not in valid_employer_codes:
            print(f"⚠ Row {row_num}: Invalid destination employer '{dest_code}', skipping")
            skipped_fk_errors += 1
            continue
        
        if contract_code not in valid_contract_codes:
            print(f"⚠ Row {row_num}: Invalid contract '{contract_code}', skipping")
            skipped_fk_errors += 1
            continue
        
        # Validation 2: Check balance (Business Logic)
        try:
            current_balance = calculate_real_balance(db, source_code, fiscal_year)
            
            if current_balance < amount:
                print(f"⚠ Row {row_num}: INSUFFICIENT FUNDS for employer '{source_code}'")
                print(f"  Current balance: {current_balance:,.0f} Rials")
                print(f"  Transfer amount: {amount:,.0f} Rials")
                print(f"  Deficit: {(amount - current_balance):,.0f} Rials")
                skipped_insufficient_funds += 1
                continue
                
        except Exception as e:
            print(f"⚠ Row {row_num}: Error calculating balance: {e}, skipping")
            skipped_fk_errors += 1
            continue
        
        # Insert valid row
        try:
            credit_transfer = CreditTransfer(
                source_employer_code=source_code,
                destination_employer_code=dest_code,
                broker_name=broker,
                fiscal_year=fiscal_year,
                amount=amount,
                contract_tracking_code=contract_code
            )
            
            db.add(credit_transfer)
            inserted_rows += 1
            
            if inserted_rows % 10 == 0:
                print(f"✓ Processed {inserted_rows} valid transfers...")
                
        except Exception as e:
            print(f"✗ Row {row_num}: Database error: {e}")
            skipped_fk_errors += 1
            continue
    
    # Step 6: Commit and close
    print("\n[6/6] Committing changes...")
    try:
        db.commit()
        print("✓ All changes committed successfully")
    except Exception as e:
        print(f"✗ Error committing changes: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"Total rows in Excel:              {total_rows}")
    print(f"Successfully inserted:            {inserted_rows}")
    print(f"Skipped (FK/validation errors):   {skipped_fk_errors}")
    print(f"Skipped (insufficient funds):     {skipped_insufficient_funds}")
    print(f"Total skipped:                    {skipped_fk_errors + skipped_insufficient_funds}")
    print("=" * 70)
    
    success_rate = (inserted_rows / total_rows * 100) if total_rows > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    print("\n✓ Import process completed!\n")


if __name__ == "__main__":
    import_credit_transfers()
