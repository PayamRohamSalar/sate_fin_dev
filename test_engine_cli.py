#!/usr/bin/env python3
"""
CLI Test Script for Financial Engine
=====================================
This script directly tests the calculate_real_balance function from the financial engine
by fetching a real employer from the database and calculating their balance.
"""

from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.financial_engine import calculate_real_balance
from models.employer import Employer


def test_financial_engine():
    """
    Test the financial engine by calculating balance for a real employer from the database.
    """
    print("=" * 70)
    print("SATE Financial Engine - CLI Test")
    print("=" * 70)
    
    # Initialize database session
    db: Session = SessionLocal()
    
    try:
        # Fetch one employer from the database dynamically
        employer = db.query(Employer).filter(
            Employer.is_deleted == False
        ).first()
        
        if not employer:
            print("\n❌ No employers found in the database.")
            print("Please ensure the database is populated with employer data.")
            return
        
        print(f"\n✓ Found Employer: {employer.name}")
        print(f"  Classification Code: {employer.classification_code}")
        print(f"  Parent Code: {employer.parent_code or 'N/A (Top-level employer)'}")
        
        # Test for multiple funding years
        test_years = [1402, 1403, 1404]
        
        print(f"\n{'Year':<10} {'Balance (Rials)':<20} {'Status':<15}")
        print("-" * 70)
        
        for year in test_years:
            try:
                balance = calculate_real_balance(
                    db=db,
                    employer_code=employer.classification_code,
                    funding_year=year
                )
                
                # Format the balance with thousand separators
                balance_formatted = f"{balance:,.2f}"
                status = "✓ Success"
                
                print(f"{year:<10} {balance_formatted:<20} {status:<15}")
                
            except Exception as e:
                print(f"{year:<10} {'Error':<20} ❌ {str(e)}")
        
        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        print("\n✓ Database connection closed.")


if __name__ == "__main__":
    test_financial_engine()
