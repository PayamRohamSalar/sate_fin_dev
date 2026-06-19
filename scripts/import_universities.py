import pandas as pd
import sys
from pathlib import Path
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from models.university import University


def import_universities():
    """Import universities from Excel file"""
    
    # Drop universities table with CASCADE to handle FK dependencies
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS universities CASCADE"))
    print("[OK] Dropped universities table with CASCADE")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
    
    # Read Excel file
    excel_path = "data/Universities.xlsx"
    print(f"Reading Excel from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        print(f"[OK] Loaded {len(df)} rows from Excel")
    except FileNotFoundError:
        print(f"[ERROR] Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading Excel: {e}")
        return
    
    # Display column count (avoid printing Persian characters)
    print(f"Excel has {len(df.columns)} columns")
    
    # Column mapping (Persian headers to model fields)
    column_mapping = {
        'کد رهگیری': 'tracking_code',
        'شناسه ملی موسسه': 'national_id',
        'نام موسسه': 'name',
        'شهر': 'city',
        'آدرس': 'address',
        'استان موسسه': 'province',
        'نوع موسسه': 'university_type',
        'وضعیت': 'status'
    }
    
    # Start database session
    session = Session(bind=engine)
    
    try:
        # Performance optimization: Query existing national_ids once
        print("Fetching existing university records...")
        existing_ids = set(
            national_id for (national_id,) in session.query(University.national_id).all()
        )
        print(f"[OK] Found {len(existing_ids)} existing universities in database")
        
        # Counters
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        print("\nProcessing records...")
        
        # Iterate through dataframe
        for index, row in df.iterrows():
            try:
                # Get national_id (primary key)
                national_id = row.get('شناسه ملی موسسه')
                
                # Convert pandas NaN to None and strip whitespaces
                national_id = None if pd.isna(national_id) else str(national_id).strip()
                
                # Skip if national_id is empty or already exists
                if not national_id:
                    skipped_count += 1
                    continue
                    
                if national_id in existing_ids:
                    skipped_count += 1
                    continue
                
                # Prepare university data
                university_data = {}
                for persian_col, field_name in column_mapping.items():
                    value = row.get(persian_col)
                    # Convert NaN to None, strip strings
                    if pd.isna(value):
                        university_data[field_name] = None
                    elif isinstance(value, str):
                        university_data[field_name] = value.strip()
                    else:
                        university_data[field_name] = value
                
                # Handle NOT NULL constraints - provide defaults for required fields
                # If university_type is None, set a default value
                if university_data.get('university_type') is None:
                    university_data['university_type'] = 'نامشخص'
                
                # If province is None, set a default value
                if university_data.get('province') is None:
                    university_data['province'] = 'نامشخص'
                
                # If name is None, skip this record
                if university_data.get('name') is None:
                    skipped_count += 1
                    continue
                
                # If status is None, set default
                if university_data.get('status') is None:
                    university_data['status'] = 'فعال'
                
                # Create University instance
                university = University(**university_data)
                session.add(university)
                
                # Add to existing_ids set to prevent duplicates in same batch
                existing_ids.add(national_id)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    session.commit()
                    print(f"  Progress: {added_count} universities added, {skipped_count} skipped")
                
            except Exception as e:
                error_count += 1
                print(f"  Row {index + 1}: Error - {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"[OK] Successfully imported: {added_count} universities")
        print(f"[SKIP] Skipped (duplicates/empty): {skipped_count}")
        print(f"[ERROR] Errors: {error_count}")
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
    print("UNIVERSITY IMPORT SCRIPT")
    print("="*60)
    import_universities()
