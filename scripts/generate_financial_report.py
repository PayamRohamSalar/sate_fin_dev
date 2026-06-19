"""
Financial Report Generator
Calculates employer balances by comparing mandated budgets against actual payments.
"""

import pandas as pd
import os
from pathlib import Path
from sqlalchemy import create_engine

# Import database engine
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import engine


def main():
    print("=" * 60)
    print("Financial Report Generator - Employer Balance Analysis")
    print("=" * 60)
    
    # Step 1: Extract data from database
    print("\n[1/5] Extracting data from database...")
    
    try:
        # Read tables into DataFrames
        df_employers = pd.read_sql_table('employers', con=engine)
        print(f"   ✓ Loaded {len(df_employers)} employers")
        
        df_mandates = pd.read_sql_table('annual_mandates', con=engine)
        print(f"   ✓ Loaded {len(df_mandates)} annual mandates")
        
        df_contracts = pd.read_sql_table('contracts', con=engine)
        print(f"   ✓ Loaded {len(df_contracts)} contracts")
        
        df_payments = pd.read_sql_table('payments', con=engine)
        print(f"   ✓ Loaded {len(df_payments)} payments")
        
    except Exception as e:
        print(f"   ✗ Error reading tables: {e}")
        return
    
    # Step 2: Aggregate payments by employer and funding year
    print("\n[2/5] Aggregating payments by employer and funding year...")
    
    # Merge payments with contracts to get employer_code for each payment
    df_payments_with_employer = df_payments.merge(
        df_contracts[['tracking_code', 'employer_code']],
        left_on='contract_tracking_code',
        right_on='tracking_code',
        how='left'
    )
    
    # Group by employer and funding year, sum the amounts
    df_payment_aggregates = df_payments_with_employer.groupby(
        ['employer_code', 'funding_year']
    )['amount'].sum().reset_index()
    
    df_payment_aggregates.rename(columns={'amount': 'total_payments'}, inplace=True)
    print(f"   ✓ Aggregated payments for {len(df_payment_aggregates)} employer-year combinations")
    
    # Step 3: Calculate balance
    print("\n[3/5] Calculating financial balances...")
    
    # Merge mandates with payment aggregates
    df_balance = df_mandates.merge(
        df_payment_aggregates,
        left_on=['employer_code', 'fiscal_year'],
        right_on=['employer_code', 'funding_year'],
        how='outer'
    )
    
    # Fill NaN values with 0
    df_balance['mandated_amount'] = df_balance['mandated_amount'].fillna(0)
    df_balance['total_payments'] = df_balance['total_payments'].fillna(0)
    
    # Use fiscal_year as the primary year column (coalesce with funding_year if needed)
    df_balance['year'] = df_balance['fiscal_year'].fillna(df_balance['funding_year']).astype(int)
    
    # Calculate balance
    df_balance['balance'] = df_balance['mandated_amount'] - df_balance['total_payments']
    
    print(f"   ✓ Calculated balances for {len(df_balance)} records")
    
    # Step 4: Format output with employer names
    print("\n[4/5] Formatting final report with employer names...")
    
    # Merge with employers to get names
    df_final = df_balance.merge(
        df_employers[['classification_code', 'name']],
        left_on='employer_code',
        right_on='classification_code',
        how='left'
    )
    
    # Select and rename columns to Persian
    df_final = df_final[[
        'employer_code',
        'name',
        'year',
        'mandated_amount',
        'total_payments',
        'balance'
    ]]
    
    df_final.columns = [
        'کد مشمول',
        'نام مشمول',
        'سال مالی',
        'اعتبار تکلیفی (ریال)',
        'جمع پرداختی (ریال)',
        'مانده (ریال)'
    ]
    
    # Sort by employer code and year
    df_final = df_final.sort_values(['کد مشمول', 'سال مالی'])
    
    print(f"   ✓ Final report contains {len(df_final)} rows")
    
    # Step 5: Export to Excel
    print("\n[5/5] Exporting to Excel...")
    
    # Ensure results directory exists
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    output_path = results_dir / 'financial_report_summary.xlsx'
    
    try:
        df_final.to_excel(output_path, index=False, engine='openpyxl')
        print(f"   ✓ Exported to: {output_path}")
    except Exception as e:
        print(f"   ✗ Error exporting to Excel: {e}")
        return
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("REPORT SUMMARY")
    print("=" * 60)
    print(f"Total employers: {df_final['کد مشمول'].nunique()}")
    print(f"Total fiscal years: {df_final['سال مالی'].nunique()}")
    print(f"Total mandated amount: {df_final['اعتبار تکلیفی (ریال)'].sum():,.0f} Rials")
    print(f"Total payments: {df_final['جمع پرداختی (ریال)'].sum():,.0f} Rials")
    print(f"Total remaining balance: {df_final['مانده (ریال)'].sum():,.0f} Rials")
    print("=" * 60)
    print("\n✓ Financial report generation completed successfully!")


if __name__ == '__main__':
    main()
