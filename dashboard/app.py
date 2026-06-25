import streamlit as st
import pandas as pd
import io
from sqlalchemy import func, case
from sqlalchemy.orm import Session
import sys
import os
import plotly.graph_objects as go

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine
from models.employer import Employer
from models.deposits import AnnualMandate, DepositReceipt
from models.payment import Payment
from models.contract import Contract
from models.transfer import CreditTransfer


def to_persian_numbers(text):
    """
    Convert English digits to Persian digits and format numbers with thousand separators.
    Handles strings, integers, floats, and already-formatted strings.
    """
    # Persian digit mapping
    persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    
    # If it's a number, format it first with commas
    if isinstance(text, (int, float)):
        text = f"{int(text):,}"
    else:
        text = str(text)
    
    # Replace English digits with Persian
    for eng, per in persian_digits.items():
        text = text.replace(eng, per)
    
    return text


def get_active_employers(db: Session):
    """Fetch all active employers for dropdown."""
    employers = db.query(Employer).filter(
        Employer.status == 'Active',
        Employer.is_deleted == False
    ).order_by(Employer.name).all()
    return employers


def get_employer_financials(db: Session, employer_code: str):
    """
    Fetch and aggregate financial data for a specific employer across all years.
    Returns a DataFrame with columns for each financial metric by year.
    """
    
    # Get the employer details to check if it's a Mother entity
    employer = db.query(Employer).filter(Employer.classification_code == employer_code).first()
    if not employer:
        return pd.DataFrame()
    
    # Determine which codes to include (main + subsidiaries for Mother entities)
    if employer.employer_type == 'Mother':
        codes_to_include = [employer_code]
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer_code,
            Employer.is_deleted == False
        ).all()
        codes_to_include.extend([s[0] for s in subsidiaries])
    else:
        codes_to_include = [employer_code]
    
    # 1. Get Annual Mandates
    mandates_query = db.query(
        AnnualMandate.fiscal_year.label('year'),
        func.sum(AnnualMandate.mandated_amount).label('mandated_amount')
    ).filter(
        AnnualMandate.employer_code.in_(codes_to_include),
        AnnualMandate.is_deleted == False
    ).group_by(AnnualMandate.fiscal_year)
    
    df_mandates = pd.read_sql(mandates_query.statement, db.bind)
    
    # 2. Get Deposit Receipts
    deposits_query = db.query(
        DepositReceipt.fiscal_year.label('year'),
        func.sum(DepositReceipt.deposit_amount).label('deposit_amount')
    ).filter(
        DepositReceipt.employer_code.in_(codes_to_include),
        DepositReceipt.is_deleted == False
    ).group_by(DepositReceipt.fiscal_year)
    
    df_deposits = pd.read_sql(deposits_query.statement, db.bind)
    
    # 3. Get Payments (via Contract relationship)
    payments_query = db.query(
        Payment.funding_year.label('year'),
        func.sum(Payment.amount).label('payment_amount')
    ).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code.in_(codes_to_include),
        Payment.is_deleted == False,
        Contract.is_deleted == False
    ).group_by(Payment.funding_year)
    
    df_payments = pd.read_sql(payments_query.statement, db.bind)
    
    # 4. Get Transfers IN (where this employer is the destination)
    transfers_in_query = db.query(
        CreditTransfer.fiscal_year.label('year'),
        func.sum(CreditTransfer.amount).label('transfer_in')
    ).filter(
        CreditTransfer.destination_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False
    ).group_by(CreditTransfer.fiscal_year)
    
    df_transfers_in = pd.read_sql(transfers_in_query.statement, db.bind)
    
    # 5. Get Transfers OUT (where this employer is the source)
    transfers_out_query = db.query(
        CreditTransfer.fiscal_year.label('year'),
        func.sum(CreditTransfer.amount).label('transfer_out')
    ).filter(
        CreditTransfer.source_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False
    ).group_by(CreditTransfer.fiscal_year)
    
    df_transfers_out = pd.read_sql(transfers_out_query.statement, db.bind)
    
    # Merge all dataframes on year
    dfs = [df_mandates, df_deposits, df_payments, df_transfers_in, df_transfers_out]
    df_merged = dfs[0]
    
    for df in dfs[1:]:
        df_merged = df_merged.merge(df, on='year', how='outer')
    
    # Fill NaN with 0
    df_merged = df_merged.fillna(0)
    
    # Sort by year
    df_merged = df_merged.sort_values('year')
    
    # Calculate balance: (Deposits + Transfers IN) - (Payments + Transfers OUT)
    df_merged['balance'] = (
        df_merged['deposit_amount'] + df_merged['transfer_in']
    ) - (
        df_merged['payment_amount'] + df_merged['transfer_out']
    )
    
    return df_merged


def get_all_employers_financials(db: Session):
    """
    Fetch and aggregate financial data for ALL employers across ALL years.
    Returns a DataFrame with one row per (employer, year) combination.
    """
    
    # Get all active employers
    employers = db.query(Employer).filter(
        Employer.status == 'Active',
        Employer.is_deleted == False
    ).all()
    
    all_data = []
    
    for employer in employers:
        employer_code = employer.classification_code
        employer_name = employer.name
        
        # Determine which codes to include (main + subsidiaries for Mother entities)
        if employer.employer_type == 'Mother':
            codes_to_include = [employer_code]
            subsidiaries = db.query(Employer.classification_code).filter(
                Employer.parent_code == employer_code,
                Employer.is_deleted == False
            ).all()
            codes_to_include.extend([s[0] for s in subsidiaries])
        else:
            codes_to_include = [employer_code]
        
        # Get Annual Mandates
        mandates_query = db.query(
            AnnualMandate.fiscal_year.label('year'),
            func.sum(AnnualMandate.mandated_amount).label('mandated_amount')
        ).filter(
            AnnualMandate.employer_code.in_(codes_to_include),
            AnnualMandate.is_deleted == False
        ).group_by(AnnualMandate.fiscal_year)
        
        df_mandates = pd.read_sql(mandates_query.statement, db.bind)
        
        # Get Deposit Receipts
        deposits_query = db.query(
            DepositReceipt.fiscal_year.label('year'),
            func.sum(DepositReceipt.deposit_amount).label('deposit_amount')
        ).filter(
            DepositReceipt.employer_code.in_(codes_to_include),
            DepositReceipt.is_deleted == False
        ).group_by(DepositReceipt.fiscal_year)
        
        df_deposits = pd.read_sql(deposits_query.statement, db.bind)
        
        # Get Payments
        payments_query = db.query(
            Payment.funding_year.label('year'),
            func.sum(Payment.amount).label('payment_amount')
        ).join(
            Contract, Payment.contract_tracking_code == Contract.tracking_code
        ).filter(
            Contract.employer_code.in_(codes_to_include),
            Payment.is_deleted == False,
            Contract.is_deleted == False
        ).group_by(Payment.funding_year)
        
        df_payments = pd.read_sql(payments_query.statement, db.bind)
        
        # Get Transfers IN
        transfers_in_query = db.query(
            CreditTransfer.fiscal_year.label('year'),
            func.sum(CreditTransfer.amount).label('transfer_in')
        ).filter(
            CreditTransfer.destination_employer_code.in_(codes_to_include),
            CreditTransfer.is_deleted == False
        ).group_by(CreditTransfer.fiscal_year)
        
        df_transfers_in = pd.read_sql(transfers_in_query.statement, db.bind)
        
        # Get Transfers OUT
        transfers_out_query = db.query(
            CreditTransfer.fiscal_year.label('year'),
            func.sum(CreditTransfer.amount).label('transfer_out')
        ).filter(
            CreditTransfer.source_employer_code.in_(codes_to_include),
            CreditTransfer.is_deleted == False
        ).group_by(CreditTransfer.fiscal_year)
        
        df_transfers_out = pd.read_sql(transfers_out_query.statement, db.bind)
        
        # Merge all dataframes
        dfs = [df_mandates, df_deposits, df_payments, df_transfers_in, df_transfers_out]
        df_merged = dfs[0] if not dfs[0].empty else pd.DataFrame(columns=['year'])
        
        for df in dfs[1:]:
            if not df.empty:
                df_merged = df_merged.merge(df, on='year', how='outer')
        
        # Fill NaN with 0
        df_merged = df_merged.fillna(0)
        
        # Add employer info
        df_merged['employer_code'] = employer_code
        df_merged['employer_name'] = employer_name
        
        # Calculate balance
        df_merged['balance'] = (
            df_merged['mandated_amount'] + df_merged['deposit_amount'] + df_merged['transfer_in']
        ) - (
            df_merged['payment_amount'] + df_merged['transfer_out']
        )
        
        all_data.append(df_merged)
    
    # Concatenate all employers
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        # Reorder columns
        df_all = df_all[['employer_code', 'employer_name', 'year', 'mandated_amount', 
                         'deposit_amount', 'payment_amount', 'transfer_in', 
                         'transfer_out', 'balance']]
        return df_all
    else:
        return pd.DataFrame()


def format_number(value):
    """Format numbers with comma separators and no decimals (kept for raw data)."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "0"


def to_excel(df):
    """
    Write a DataFrame to a BytesIO buffer as an Excel file and return the bytes.
    This uses the raw numeric DataFrame before Persian digit conversion.
    """
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()


def main():
    st.set_page_config(
        page_title="\u062f\u0627\u0634\u0628\u0648\u0631\u062f \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc \u0633\u0627\u062a\u0639",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject CSS for Persian font (Vazirmatn), RTL layout, centered title & table styling
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');

        html, body, [class*="css"], * {
            font-family: 'Vazirmatn', sans-serif !important;
            direction: rtl;
            text-align: right;
        }

        h1, .stHeadingContainer {
            text-align: center !important;
            direction: rtl;
        }

        table, th, td, [data-testid="stTable"] {
            font-family: 'Vazirmatn', sans-serif !important;
            font-size: 16px !important;
            text-align: center !important;
            direction: rtl;
        }

        th {
            background-color: #f0f2f6 !important;
            border-bottom: 2px solid #4a4a4a !important;
            font-weight: 700 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("\U0001f4ca \u062f\u0627\u0634\u0628\u0648\u0631\u062f \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc \u0633\u0627\u062a\u0639 - \u062a\u0631\u0627\u0632\u0646\u0627\u0645\u0647 \u0645\u0634\u0645\u0648\u0644\u06cc\u0646")
    st.markdown("---")
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Get active employers for dropdown
        employers = get_active_employers(db)
        
        if not employers:
            st.warning("\u0647\u06cc\u0686 \u0645\u0634\u0645\u0648\u0644\u06cc \u0641\u0639\u0627\u0644 \u062f\u0631 \u0633\u06cc\u0633\u062a\u0645 \u06cc\u0627\u0641\u062a \u0646\u0634\u062f.")
            return
        
        # Create tabs
        tab1, tab2 = st.tabs(['\u062a\u0631\u0627\u0632\u0646\u0627\u0645\u0647 \u0645\u0634\u0645\u0648\u0644\u06cc\u0646', '\u0646\u0645\u0627\u06cc \u06a9\u0644\u0627\u0646 (Executive Summary)'])
        
        # ─── Tab 1: Employer-Specific View ───
        with tab1:
            # Create employer selection dropdown
            employer_options = {emp.classification_code: f"{emp.name} ({emp.classification_code})" for emp in employers}

            # Default to employer with classification_code '231500', fallback to 0
            default_index = 0
            employer_keys = list(employer_options.keys())
            if '231500' in employer_keys:
                default_index = employer_keys.index('231500')

            selected_code = st.selectbox(
                "\u0627\u0646\u062a\u062e\u0627\u0628 \u0645\u0634\u0645\u0648\u0644:",
                options=employer_keys,
                format_func=lambda x: employer_options[x],
                index=default_index
            )
            
            if selected_code:
                # Get selected employer details
                selected_employer = next(emp for emp in employers if emp.classification_code == selected_code)
                
                # Display employer info
                st.subheader(f"\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0645\u0634\u0645\u0648\u0644: {selected_employer.name}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**\u06a9\u062f \u0637\u0628\u0642\u0647\u200c\u0628\u0646\u062f\u06cc:** {selected_employer.classification_code}")
                with col2:
                    st.info(f"**\u0627\u0633\u062a\u0627\u0646:** {selected_employer.province}")
                with col3:
                    st.info(f"**\u0633\u0627\u0632\u0645\u0627\u0646 \u0628\u0627\u0644\u0627\u062f\u0633\u062a:** {selected_employer.upper_organization}")
                
                st.markdown("---")
                
                # Fetch financial data
                with st.spinner("\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0645\u0627\u0644\u06cc..."):
                    df = get_employer_financials(db, selected_code)
                
                if df.empty:
                    st.warning("\u0647\u06cc\u0686 \u062f\u0627\u062f\u0647 \u0645\u0627\u0644\u06cc \u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u0645\u0634\u0645\u0648\u0644 \u06cc\u0627\u0641\u062a \u0646\u0634\u062f.")
                else:
                    # Calculate totals for KPIs
                    total_mandated = df['mandated_amount'].sum()
                    total_deposits = df['deposit_amount'].sum()
                    total_payments = df['payment_amount'].sum()
                    total_transfer_in = df['transfer_in'].sum()
                    total_transfer_out = df['transfer_out'].sum()
                    total_balance = df['balance'].sum()
                    
                    # Display KPI metrics with Persian numbers
                    st.subheader("\U0001f511 \u0634\u0627\u062e\u0635\u200c\u0647\u0627\u06cc \u06a9\u0644\u06cc\u062f\u06cc")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("\u0627\u0639\u062a\u0628\u0627\u0631 \u062a\u06a9\u0644\u06cc\u0641\u06cc (\u06a9\u0644)", to_persian_numbers(total_mandated))
                        st.metric("\u0648\u0627\u0631\u06cc\u0632\u06cc (\u06a9\u0644)", to_persian_numbers(total_deposits))
                    with col2:
                        st.metric("\u0647\u0632\u06cc\u0646\u0647 \u06a9\u0631\u062f (\u06a9\u0644)", to_persian_numbers(total_payments))
                        st.metric("\u0627\u0646\u062a\u0642\u0627\u0644 \u0648\u0631\u0648\u062f\u06cc (\u06a9\u0644)", to_persian_numbers(total_transfer_in))
                    with col3:
                        st.metric("\u0627\u0646\u062a\u0642\u0627\u0644 \u062e\u0631\u0648\u062c\u06cc (\u06a9\u0644)", to_persian_numbers(total_transfer_out))
                        st.metric("\u0645\u0627\u0646\u062f\u0647 \u0646\u0647\u0627\u06cc\u06cc (\u06a9\u0644)", to_persian_numbers(total_balance))
                    
                    st.markdown("---")
                    st.subheader("\U0001f4cb \u062c\u062f\u0648\u0644 \u062a\u0641\u0635\u06cc\u0644\u06cc \u0628\u0647 \u062a\u0641\u06a9\u06cc\u06a9 \u0633\u0627\u0644")
                    
                    # Prepare display DataFrame with Persian digits
                    df_display = df.copy()
                    df_display = df_display.rename(columns={
                        'year': '\u0633\u0627\u0644 \u0645\u0627\u0644\u06cc',
                        'mandated_amount': '\u0627\u0639\u062a\u0628\u0627\u0631 \u062a\u06a9\u0644\u06cc\u0641\u06cc',
                        'deposit_amount': '\u0645\u062c\u0645\u0648\u0639 \u0648\u0627\u0631\u06cc\u0632\u06cc',
                        'payment_amount': '\u0647\u0632\u06cc\u0646\u0647 \u06a9\u0631\u062f',
                        'transfer_in': '\u0627\u0646\u062a\u0642\u0627\u0644 \u0648\u0631\u0648\u062f\u06cc',
                        'transfer_out': '\u0627\u0646\u062a\u0642\u0627\u0644 \u062e\u0631\u0648\u062c\u06cc',
                        'balance': '\u0645\u0627\u0646\u062f\u0647 \u0648\u0627\u0642\u0639\u06cc'
                    })
                    
                    # Apply Persian numbers to all columns
                    for col in ['\u0633\u0627\u0644 \u0645\u0627\u0644\u06cc']:
                        df_display[col] = df_display[col].apply(to_persian_numbers)
                        
                    for col in ['\u0627\u0639\u062a\u0628\u0627\u0631 \u062a\u06a9\u0644\u06cc\u0641\u06cc', '\u0645\u062c\u0645\u0648\u0639 \u0648\u0627\u0631\u06cc\u0632\u06cc', '\u0647\u0632\u06cc\u0646\u0647 \u06a9\u0631\u062f', '\u0627\u0646\u062a\u0642\u0627\u0644 \u0648\u0631\u0648\u062f\u06cc', '\u0627\u0646\u062a\u0642\u0627\u0644 \u062e\u0631\u0648\u062c\u06cc', '\u0645\u0627\u0646\u062f\u0647 \u0648\u0627\u0642\u0639\u06cc']:
                        df_display[col] = df_display[col].apply(to_persian_numbers)
                    
                    # Display the table (using st.table for proper CSS styling)
                    st.table(df_display)
                    
                    # Excel download button (uses raw df with English digits for Excel compatibility)
                    df_excel = df.copy()
                    df_excel = df_excel.rename(columns={
                        'year': '\u0633\u0627\u0644 \u0645\u0627\u0644\u06cc',
                        'mandated_amount': '\u0627\u0639\u062a\u0628\u0627\u0631 \u062a\u06a9\u0644\u06cc\u0641\u06cc',
                        'deposit_amount': '\u0645\u062c\u0645\u0648\u0639 \u0648\u0627\u0631\u06cc\u0632\u06cc',
                        'payment_amount': '\u0647\u0632\u06cc\u0646\u0647 \u06a9\u0631\u062f',
                        'transfer_in': '\u0627\u0646\u062a\u0642\u0627\u0644 \u0648\u0631\u0648\u062f\u06cc',
                        'transfer_out': '\u0627\u0646\u062a\u0642\u0627\u0644 \u062e\u0631\u0648\u062c\u06cc',
                        'balance': '\u0645\u0627\u0646\u062f\u0647 \u0648\u0627\u0642\u0639\u06cc'
                    })
                    
                    st.download_button(
                        label="\U0001f4e5 \u062f\u0627\u0646\u0644\u0648\u062f \u06af\u0632\u0627\u0631\u0634 \u0628\u0647 \u0635\u0648\u0631\u062a \u0627\u06a9\u0633\u0644",
                        data=to_excel(df_excel),
                        file_name=f"financial_report_{selected_code}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    
                    # Additional analysis
                    st.markdown("---")
                    st.subheader("\U0001f4ca \u062a\u062d\u0644\u06cc\u0644 \u0648 \u0646\u0645\u0648\u062f\u0627\u0631")
                    
                    # Create a chart showing deposits vs payments over years with Persian font
                    chart_data = df[['year', 'deposit_amount', 'payment_amount', 'balance']].copy()
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=chart_data['year'],
                        y=chart_data['deposit_amount'],
                        mode='lines+markers',
                        name='\u0648\u0627\u0631\u06cc\u0632\u06cc',
                        line=dict(color='green', width=2)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=chart_data['year'],
                        y=chart_data['payment_amount'],
                        mode='lines+markers',
                        name='\u0647\u0632\u06cc\u0646\u0647',
                        line=dict(color='red', width=2)
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=chart_data['year'],
                        y=chart_data['balance'],
                        mode='lines+markers',
                        name='\u0645\u0627\u0646\u062f\u0647',
                        line=dict(color='blue', width=2)
                    ))
                    
                    fig.update_layout(
                        font=dict(family='Vazirmatn', size=14),
                        xaxis_title='\u0633\u0627\u0644 \u0645\u0627\u0644\u06cc',
                        yaxis_title='\u0645\u0628\u0644\u063a (\u0631\u06cc\u0627\u0644)',
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        # ─── Tab 2: Executive Summary (Macro View) ───
        with tab2:
            st.subheader("\U0001f3e2 \u0646\u0645\u0627\u06cc \u06a9\u0644\u0627\u0646 - \u062e\u0644\u0627\u0635\u0647 \u0645\u062f\u06cc\u0631\u06cc\u062a\u06cc")
            
            with st.spinner("\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u06a9\u0644\u0627\u0646..."):
                df_all = get_all_employers_financials(db)
            
            if df_all.empty:
                st.warning("\u0647\u06cc\u0686 \u062f\u0627\u062f\u0647 \u0645\u0627\u0644\u06cc \u062f\u0631 \u0633\u06cc\u0633\u062a\u0645 \u06cc\u0627\u0641\u062a \u0646\u0634\u062f.")
            else:
                # ── Global KPIs ──
                grand_mandated = df_all['mandated_amount'].sum()
                grand_deposits = df_all['deposit_amount'].sum()
                grand_payments = df_all['payment_amount'].sum()
                grand_balance = df_all['balance'].sum()
                
                st.markdown("### \U0001f511 \u0634\u0627\u062e\u0635\u200c\u0647\u0627\u06cc \u06a9\u0644\u06cc\u062f\u06cc \u06a9\u0644 \u0633\u06cc\u0633\u062a\u0645")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("\u0627\u0639\u062a\u0628\u0627\u0631 \u062a\u06a9\u0644\u06cc\u0641\u06cc (\u06a9\u0644 \u0633\u06cc\u0633\u062a\u0645)", to_persian_numbers(grand_mandated))
                with col2:
                    st.metric("\u0645\u062c\u0645\u0648\u0639 \u0648\u0627\u0631\u06cc\u0632\u06cc (\u06a9\u0644 \u0633\u06cc\u0633\u062a\u0645)", to_persian_numbers(grand_deposits))
                with col3:
                    st.metric("\u0647\u0632\u06cc\u0646\u0647 \u06a9\u0631\u062f (\u06a9\u0644 \u0633\u06cc\u0633\u062a\u0645)", to_persian_numbers(grand_payments))
                with col4:
                    st.metric("\u0645\u0627\u0646\u062f\u0647 \u0648\u0627\u0642\u0639\u06cc (\u06a9\u0644 \u0633\u06cc\u0633\u062a\u0645)", to_persian_numbers(grand_balance))
                
                st.markdown("---")
                
                # ── Top 10 Employers by Deposit Amount ──
                st.markdown("### \U0001f4ca \u06f1\u06f0 \u0645\u0634\u0645\u0648\u0644 \u0628\u0631\u062a\u0631 \u0628\u0631 \u0627\u0633\u0627\u0633 \u0645\u06cc\u0632\u0627\u0646 \u0648\u0627\u0631\u06cc\u0632\u06cc")
                
                top10 = df_all.groupby(
                    ['employer_code', 'employer_name'], as_index=False
                )['deposit_amount'].sum().nlargest(10, 'deposit_amount')
                
                fig_top10 = go.Figure(go.Bar(
                    x=top10['deposit_amount'],
                    y=top10['employer_name'],
                    orientation='h',
                    text=top10['deposit_amount'].apply(lambda v: to_persian_numbers(int(v))),
                    textposition='auto',
                    marker_color='#2196F3'
                ))
                
                fig_top10.update_layout(
                    font=dict(family='Vazirmatn', size=14),
                    xaxis_title='\u0645\u0628\u0644\u063a \u0648\u0627\u0631\u06cc\u0632\u06cc (\u0631\u06cc\u0627\u0644)',
                    yaxis_title='',
                    yaxis=dict(autorange='reversed'),
                    height=500,
                    margin=dict(l=20, r=20, t=40, b=40)
                )
                
                st.plotly_chart(fig_top10, use_container_width=True)
                
                st.markdown("---")
                
                # ── Global Excel Export ──
                df_export = df_all.copy()
                df_export = df_export.rename(columns={
                    'employer_code': '\u06a9\u062f \u0645\u0634\u0645\u0648\u0644',
                    'employer_name': '\u0646\u0627\u0645 \u0645\u0634\u0645\u0648\u0644',
                    'year': '\u0633\u0627\u0644 \u0645\u0627\u0644\u06cc',
                    'mandated_amount': '\u0627\u0639\u062a\u0628\u0627\u0631 \u062a\u06a9\u0644\u06cc\u0641\u06cc',
                    'deposit_amount': '\u0645\u062c\u0645\u0648\u0639 \u0648\u0627\u0631\u06cc\u0632\u06cc',
                    'payment_amount': '\u0647\u0632\u06cc\u0646\u0647 \u06a9\u0631\u062f',
                    'transfer_in': '\u0627\u0646\u062a\u0642\u0627\u0644 \u0648\u0631\u0648\u062f\u06cc',
                    'transfer_out': '\u0627\u0646\u062a\u0642\u0627\u0644 \u062e\u0631\u0648\u062c\u06cc',
                    'balance': '\u0645\u0627\u0646\u062f\u0647 \u0648\u0627\u0642\u0639\u06cc'
                })
                
                st.download_button(
                    label="\U0001f4e5 \u062f\u0627\u0646\u0644\u0648\u062f \u06af\u0632\u0627\u0631\u0634 \u062c\u0627\u0645\u0639 \u06a9\u0644 \u0645\u0634\u0645\u0648\u0644\u06cc\u0646 (\u0627\u06a9\u0633\u0644)",
                    data=to_excel(df_export),
                    file_name="financial_report_all_employers.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            
    finally:
        db.close()


if __name__ == "__main__":
    main()
