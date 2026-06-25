"""
Credit Transfer Table Initialization Script
Safely creates the credit_transfers table without dropping existing tables.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import Base, engine
from models.transfer import CreditTransfer


def main():
    print("=" * 60)
    print("Credit Transfer Table Initialization")
    print("=" * 60)
    
    print("\nCreating credit_transfers table...")
    
    try:
        # Create only the CreditTransfer table, leaving other tables intact
        Base.metadata.create_all(bind=engine, tables=[CreditTransfer.__table__])
        
        print("✓ Successfully created credit_transfers table")
        print("\nTable structure:")
        print("  - id (Integer, Primary Key)")
        print("  - source_employer_code (String, FK -> employers)")
        print("  - destination_employer_code (String, FK -> employers, default='128342')")
        print("  - broker_name (String, nullable)")
        print("  - fiscal_year (Integer, indexed)")
        print("  - amount (Numeric(22,0))")
        print("  - contract_tracking_code (String, FK -> contracts)")
        print("  - documentation (Text, nullable)")
        print("  - created_at, updated_at, is_deleted (from SoftDeleteMixin)")
        
        print("\n" + "=" * 60)
        print("✓ Table initialization completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
