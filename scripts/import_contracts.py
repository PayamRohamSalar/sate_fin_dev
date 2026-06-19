import pandas as pd
import sys
from pathlib import Path
import io
import jdatetime
from decimal import Decimal

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from models.contract import Contract
from models.employer import Employer
from models.university import University
from models.researchers import Researcher


def parse_persian_date(date_str):
    """Parse Persian date string (e.g., '1400/05/05') to Gregorian date"""
    if pd.isna(date_str) or not date_str:
        return None
    
    try:
        # Remove any whitespace
        date_str = str(date_str).strip()
        # Parse Persian date and convert to Gregorian
        persian_date = jdatetime.datetime.strptime(date_str, '%Y/%m/%d')
        return persian_date.togregorian().date()
    except Exception as e:
        print(f"  [WARNING] Invalid date format: {date_str} - {e}")
        return None


def import_contracts():
    """Import contracts from Excel file"""
    
    # Drop contracts table with CASCADE to handle FK dependencies
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS contracts CASCADE"))
    print("[OK] Dropped contracts table with CASCADE")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
    
    # Read Excel file
    excel_path = "data/Contracts.xlsx"
    print(f"Reading Excel from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"[OK] Loaded {len(df)} rows from Excel")
    except FileNotFoundError:
        print(f"[ERROR] Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading Excel: {e}")
        return
    
    print(f"Excel has {len(df.columns)} columns")
    
    # Column mapping (Persian headers to model fields)
    column_mapping = {
        'کد رهگیری': 'tracking_code',
        'شماره طبقه بندی': 'employer_code',
        'شناسه ملی موسسه': 'university_id',
        'کد ملی فناور': 'researcher_id',
        'شناسه پیشنهاده': 'proposal_id',
        'شماره قرارداد': 'contract_number',
        'تاریخ قرارداد': 'contract_date',
        'مبلغ قرارداد(ریال)': 'total_amount',
        'عنوان قرارداد': 'title',
        'مدت زمان اجرا (ماه)': 'duration_months',
        'وضعیت': 'status'
    }
    
    # Start database session
    session = Session(bind=engine)
    
    try:
        # Performance optimization: Query all valid FK values once (avoid N+1)
        print("Fetching valid foreign key references...")
        
        valid_employer_codes = set(
            code for (code,) in session.query(Employer.classification_code).all()
        )
        print(f"[OK] Found {len(valid_employer_codes)} valid employer codes")
        
        valid_university_ids = set(
            uid for (uid,) in session.query(University.national_id).all()
        )
        print(f"[OK] Found {len(valid_university_ids)} valid university IDs")
        
        valid_researcher_ids = set(
            rid for (rid,) in session.query(Researcher.national_code).all()
        )
        print(f"[OK] Found {len(valid_researcher_ids)} valid researcher IDs")
        
        # Query existing tracking codes to avoid duplicates
        existing_tracking_codes = set(
            code for (code,) in session.query(Contract.tracking_code).all()
        )
        print(f"[OK] Found {len(existing_tracking_codes)} existing contracts in database")
        
        # Counters
        added_count = 0
        skipped_duplicate = 0
        skipped_fk_employer = 0
        skipped_fk_university = 0
        skipped_fk_researcher = 0
        skipped_invalid = 0
        error_count = 0
        
        print("\nProcessing records...")
        
        # Iterate through dataframe
        for index, row in df.iterrows():
            try:
                # Get tracking_code (primary key)
                tracking_code = row.get('کد رهگیری')
                
                # Convert pandas NaN to None and strip whitespaces
                tracking_code = None if pd.isna(tracking_code) else str(tracking_code).strip()
                
                # Skip if tracking_code is empty or already exists
                if not tracking_code:
                    skipped_invalid += 1
                    continue
                    
                if tracking_code in existing_tracking_codes:
                    skipped_duplicate += 1
                    continue
                
                # Get and validate FKs
                employer_code = row.get('شماره طبقه بندی')
                employer_code = None if pd.isna(employer_code) else str(employer_code).strip()
                
                university_id = row.get('شناسه ملی موسسه')
                university_id = None if pd.isna(university_id) else str(university_id).strip()
                
                researcher_id = row.get('کد ملی فناور')
                researcher_id = None if pd.isna(researcher_id) else str(researcher_id).strip()
                
                # Validate FK integrity - skip row if any FK is invalid
                if not employer_code or employer_code not in valid_employer_codes:
                    skipped_fk_employer += 1
                    if employer_code:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid employer_code '{employer_code}'")
                    continue
                
                if not university_id or university_id not in valid_university_ids:
                    skipped_fk_university += 1
                    if university_id:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid university_id '{university_id}'")
                    continue
                
                if not researcher_id or researcher_id not in valid_researcher_ids:
                    skipped_fk_researcher += 1
                    if researcher_id:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid researcher_id '{researcher_id}'")
                    continue
                
                # Prepare contract data
                contract_data = {
                    'tracking_code': tracking_code,
                    'employer_code': employer_code,
                    'university_id': university_id,
                    'researcher_id': researcher_id
                }
                
                # Map other fields
                for persian_col, field_name in column_mapping.items():
                    if field_name in ['tracking_code', 'employer_code', 'university_id', 'researcher_id']:
                        continue  # Already handled
                    
                    value = row.get(persian_col)
                    
                    # Handle date conversion
                    if field_name == 'contract_date':
                        contract_data[field_name] = parse_persian_date(value)
                    # Handle numeric fields
                    elif field_name == 'total_amount':
                        if pd.isna(value):
                            contract_data[field_name] = 0
                        else:
                            try:
                                contract_data[field_name] = Decimal(str(value))
                            except:
                                contract_data[field_name] = 0
                    elif field_name == 'duration_months':
                        if pd.isna(value):
                            contract_data[field_name] = None
                        else:
                            try:
                                contract_data[field_name] = int(value)
                            except:
                                contract_data[field_name] = None
                    # Handle strings
                    else:
                        if pd.isna(value):
                            contract_data[field_name] = None
                        elif isinstance(value, str):
                            contract_data[field_name] = value.strip()
                        else:
                            contract_data[field_name] = str(value)
                
                # Validate required fields
                if not contract_data.get('title'):
                    skipped_invalid += 1
                    continue
                
                # Set defaults for nullable fields
                if contract_data.get('status') is None:
                    contract_data['status'] = 'Active'
                
                # Create Contract instance
                contract = Contract(**contract_data)
                session.add(contract)
                
                # Add to existing set to prevent duplicates in same batch
                existing_tracking_codes.add(tracking_code)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    session.commit()
                    print(f"  Progress: {added_count} contracts added")
                
            except Exception as e:
                error_count += 1
                print(f"  [ERROR] Row {index + 1}: {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"[OK] Successfully imported: {added_count} contracts")
        print(f"[SKIP] Duplicates/empty tracking codes: {skipped_duplicate + skipped_invalid}")
        print(f"[FK_SKIP] Invalid employer_code: {skipped_fk_employer}")
        print(f"[FK_SKIP] Invalid university_id: {skipped_fk_university}")
        print(f"[FK_SKIP] Invalid researcher_id: {skipped_fk_researcher}")
        total_fk_skips = skipped_fk_employer + skipped_fk_university + skipped_fk_researcher
        print(f"[FK_SKIP] Total FK mismatches: {total_fk_skips}")
        print(f"[ERROR] Processing errors: {error_count}")
        print(f"Total rows processed: {len(df)}")
        print("="*60)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("="*60)
    print("CONTRACT IMPORT SCRIPT")
    print("="*60)
    import_contracts()
