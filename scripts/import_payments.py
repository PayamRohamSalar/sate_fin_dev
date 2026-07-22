import sys
import os
from datetime import datetime, date

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.date_helper import parse_strict_jalali_date
from core.database import engine, Base
from models.payment import Payment
from models.contract import Contract


def parse_jalali_date(date_str):
    """Parse a Jalali date strictly and return a Gregorian date."""
    if pd.isna(date_str) or date_str == "" or date_str is None:
        return None

    try:
        return parse_strict_jalali_date(str(date_str))
    except (TypeError, ValueError):
        return None


def clean_numeric(value):
    """Remove commas from numeric strings and convert to int."""
    if pd.isna(value):
        return 0
    
    try:
        # Convert to string, remove commas, then to int
        cleaned = str(value).replace(',', '').strip()
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0


def main():
    print("Starting Payments import...")
    
    # Read Excel file
    print("\n1. Reading Excel file...")
    df = pd.read_excel('data/Payments.xlsx')
    print(f"   Loaded {len(df)} rows from Excel")
    
    # Display column names for verification
    print(f"\n   Columns found: {df.columns.tolist()}")
    
    # Expected Persian headers
    expected_cols = [
        'سری پرداخت',
        'کد رهگیری پرداخت', 
        'کد رهگیری',
        'مبلغ پرداختی(ریال)',
        'شماره نامه ابلاغ',
        'تاریخ ابلاغ',
        'سال پرداخت',
        'پرداخت از محل سال مالی'
    ]
    
    # Verify all expected columns exist
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"\n   WARNING: Missing columns: {missing_cols}")
        return
    
    # Drop table and recreate
    print("\n2. Dropping existing payments table...")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS payments CASCADE"))
    
    print("   Creating fresh payments table...")
    Base.metadata.create_all(bind=engine, tables=[Payment.__table__])
    
    # Fetch valid contract tracking codes
    print("\n3. Fetching valid contract tracking codes...")
    session = Session(bind=engine)
    try:
        valid_contracts = set(
            session.query(Contract.tracking_code)
            .filter(Contract.is_deleted == False)
            .all()
        )
        valid_contracts = {code[0] for code in valid_contracts}
        print(f"   Found {len(valid_contracts)} valid contracts")
    finally:
        session.close()
    
    # Process payments
    print("\n4. Processing payment records...")
    session = Session(bind=engine)
    
    inserted_count = 0
    skipped_count = 0
    skipped_reasons = []
    
    try:
        for idx, row in df.iterrows():
            # Extract values
            tracking_code = str(row['کد رهگیری پرداخت']).strip() if pd.notna(row['کد رهگیری پرداخت']) else None
            contract_tracking_code = str(row['کد رهگیری']).strip() if pd.notna(row['کد رهگیری']) else None
            series = str(row['سری پرداخت']).strip() if pd.notna(row['سری پرداخت']) else None
            amount = clean_numeric(row['مبلغ پرداختی(ریال)'])
            notification_letter_number = str(row['شماره نامه ابلاغ']).strip() if pd.notna(row['شماره نامه ابلاغ']) else None
            notification_date = parse_jalali_date(row['تاریخ ابلاغ'])
            payment_year = int(row['سال پرداخت']) if pd.notna(row['سال پرداخت']) else None
            funding_year = int(row['پرداخت از محل سال مالی']) if pd.notna(row['پرداخت از محل سال مالی']) else None
            
            # Validate required fields
            if not tracking_code:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing tracking_code")
                continue
            
            if not contract_tracking_code:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing contract_tracking_code")
                continue
            
            # Validate FK integrity
            if contract_tracking_code not in valid_contracts:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Contract '{contract_tracking_code}' not found")
                continue
            
            if not payment_year or not funding_year:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing payment_year or funding_year")
                continue
            
            # Create Payment instance
            payment = Payment(
                tracking_code=tracking_code,
                contract_tracking_code=contract_tracking_code,
                series=series,
                amount=amount,
                notification_letter_number=notification_letter_number,
                notification_date=notification_date,
                payment_year=payment_year,
                funding_year=funding_year,
                attachment_path=None
            )
            
            session.add(payment)
            inserted_count += 1
        
        # Commit all changes
        session.commit()
        print(f"\n✓ Successfully inserted {inserted_count} payments")
        
        if skipped_count > 0:
            print(f"\n⚠ Skipped {skipped_count} rows due to validation errors:")
            for reason in skipped_reasons[:10]:  # Show first 10
                print(f"   - {reason}")
            if len(skipped_reasons) > 10:
                print(f"   ... and {len(skipped_reasons) - 10} more")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error during import: {e}")
        raise
    finally:
        session.close()
    
    print("\n" + "="*50)
    print("Payment import completed!")
    print(f"Total rows processed: {len(df)}")
    print(f"Successfully inserted: {inserted_count}")
    print(f"Skipped: {skipped_count}")
    print("="*50)


if __name__ == '__main__':
    main()
