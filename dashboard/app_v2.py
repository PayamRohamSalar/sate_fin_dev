import streamlit as st
import pandas as pd
import io
from sqlalchemy import func
from sqlalchemy.orm import Session
import sys
import os
import plotly.graph_objects as go

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate, DepositReceipt
from models.payment import Payment
from models.contract import Contract
from models.transfer import CreditTransfer


def to_persian_numbers(text):
    """Convert English digits to Persian digits and format numbers with thousand separators."""
    persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    if isinstance(text, (int, float)):
        text = f"{int(text):,}"
    else:
        text = str(text)
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
    """Fetch and aggregate financial data for a specific employer across all years."""
    employer = db.query(Employer).filter(Employer.classification_code == employer_code).first()
    if not employer:
        return pd.DataFrame()

    if employer.employer_type == 'Mother':
        codes_to_include = [employer_code]
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer_code,
            Employer.is_deleted == False
        ).all()
        codes_to_include.extend([s[0] for s in subsidiaries])
    else:
        codes_to_include = [employer_code]

    mandates_query = db.query(
        AnnualMandate.fiscal_year.label('year'),
        func.sum(AnnualMandate.mandated_amount).label('mandated_amount')
    ).filter(
        AnnualMandate.employer_code.in_(codes_to_include),
        AnnualMandate.is_deleted == False
    ).group_by(AnnualMandate.fiscal_year)
    df_mandates = pd.read_sql(mandates_query.statement, db.bind)

    deposits_query = db.query(
        DepositReceipt.fiscal_year.label('year'),
        func.sum(DepositReceipt.deposit_amount).label('deposit_amount')
    ).filter(
        DepositReceipt.employer_code.in_(codes_to_include),
        DepositReceipt.is_deleted == False
    ).group_by(DepositReceipt.fiscal_year)
    df_deposits = pd.read_sql(deposits_query.statement, db.bind)

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

    transfers_in_query = db.query(
        CreditTransfer.fiscal_year.label('year'),
        func.sum(CreditTransfer.amount).label('transfer_in')
    ).filter(
        CreditTransfer.destination_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_in = pd.read_sql(transfers_in_query.statement, db.bind)

    transfers_out_query = db.query(
        CreditTransfer.fiscal_year.label('year'),
        func.sum(CreditTransfer.amount).label('transfer_out')
    ).filter(
        CreditTransfer.source_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_out = pd.read_sql(transfers_out_query.statement, db.bind)

    dfs = [df_mandates, df_deposits, df_payments, df_transfers_in, df_transfers_out]
    df_merged = dfs[0]
    for df in dfs[1:]:
        df_merged = df_merged.merge(df, on='year', how='outer')
    df_merged = df_merged.fillna(0)

    df_merged['balance'] = (
        df_merged['deposit_amount'] +
        df_merged['transfer_in'] -
        df_merged['payment_amount'] -
        df_merged['transfer_out']
    )
    df_merged = df_merged.sort_values('year')
    return df_merged


def format_million_value(value) -> str:
    """Format a million-scale amount with commas and Persian digits."""
    return to_persian_numbers(round(value))


def render_kpi_card(year, mandated, adj_dep, adj_pay):
    """Render a styled HTML KPI card for a single fiscal year."""
    dep_pct = min(100, (adj_dep / mandated * 100) if mandated > 0 else 0)
    pay_pct = min(100, (adj_pay / mandated * 100) if mandated > 0 else 0)

    html_content = f'''
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); direction: rtl; font-family: 'Vazirmatn', sans-serif;">
        <h4 style="text-align: center; color: #111827;">سال {to_persian_numbers(int(year))}</h4>
        <div style="font-size: 14px; margin-bottom: 10px;">اعتبار تکلیفی: {to_persian_numbers(int(mandated))}</div>
        <div style="font-size: 14px; margin-bottom: 5px;">واریزی تعدیل‌شده: {to_persian_numbers(int(adj_dep))}</div>
        <div style="background-color: #e5e7eb; border-radius: 4px; height: 8px; margin-bottom: 15px;">
            <div style="width: {dep_pct}%; background-color: #10B981; height: 8px; border-radius: 4px;"></div>
        </div>
        <div style="font-size: 14px; margin-bottom: 5px;">هزینه‌کرد تعدیل‌شده: {to_persian_numbers(int(adj_pay))}</div>
        <div style="background-color: #e5e7eb; border-radius: 4px; height: 8px;">
            <div style="width: {pay_pct}%; background-color: #3B82F6; height: 8px; border-radius: 4px;"></div>
        </div>
    </div>
    '''
    st.markdown(html_content, unsafe_allow_html=True)


def to_excel(df: pd.DataFrame) -> bytes:
    """Convert dataframe to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Financial Report')
    output.seek(0)
    return output.getvalue()


def main():
    st.set_page_config(
        page_title="داشبورد ساتع - نسخه پیشرفته",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ─── Main Title ───
    st.markdown("<h1 style='text-align: center;'>📊 داشبورد مدیریتی ساتع - تراز مشمولین</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>(داده‌های مالی از سال ۱۴۰۲)</h3>", unsafe_allow_html=True)

    # ─── Aggressive CSS: Vazirmatn font + full RTL override ───
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    html, body, [class*="css"], * {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, .stHeadingContainer { text-align: center !important; direction: rtl; }
    table, th, td, .stTable, [data-testid="stTable"] * {
        font-family: 'Vazirmatn', sans-serif !important;
        font-size: 15px !important;
        text-align: center !important;
        direction: rtl !important;
    }
    .stPlotlyChart, .js-plotly-plot, .plotly {
        direction: ltr !important;
    }
    th { background-color: #f0f2f6 !important; border-bottom: 2px solid #4a4a4a !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")

    db = SessionLocal()

    try:
        employers = get_active_employers(db)

        if not employers:
            st.warning("هیچ مشمولی فعال در سیستم یافت نشد.")
            return

        # ─── Employer Selection ───
        employer_options = {emp.classification_code: f"{emp.name} ({emp.classification_code})" for emp in employers}
        employer_keys = list(employer_options.keys())

        default_index = 0
        if '231500' in employer_keys:
            default_index = employer_keys.index('231500')

        selected_code = st.selectbox(
            "انتخاب مشمول:",
            options=employer_keys,
            format_func=lambda x: employer_options[x],
            index=default_index
        )

        if selected_code:
            selected_employer = next(emp for emp in employers if emp.classification_code == selected_code)

            # Employer info
            st.subheader(f"اطلاعات مشمول: {selected_employer.name}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**کد طبقه‌بندی:** {selected_employer.classification_code}")
            with col2:
                st.info(f"**استان:** {selected_employer.province}")
            with col3:
                st.info(f"**سازمان بالادست:** {selected_employer.upper_organization}")

            st.markdown("---")

            # Fetch data
            with st.spinner("در حال بارگذاری اطلاعات مالی..."):
                df = get_employer_financials(db, selected_code)

            # Filter: year >= 1402
            df = df[df['year'] >= 1402]

            if df.empty:
                st.warning("هیچ داده مالی برای این مشمول از سال ۱۴۰۲ به بعد یافت نشد.")
            else:
                # Convert to millions
                financial_cols = [
                    'mandated_amount', 'deposit_amount', 'payment_amount',
                    'transfer_in', 'transfer_out', 'balance'
                ]
                df[financial_cols] = df[financial_cols] / 1_000_000

                # Visualization-only adjusted columns
                df['adjusted_deposits'] = df['deposit_amount'] + df['transfer_in']
                df['adjusted_payments'] = df['payment_amount'] + df['transfer_out']

                # ─── KPIs: HTML Cards per Year ───
                st.subheader("🔑 شاخص‌های کلیدی")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
                    unsafe_allow_html=True
                )

                years = sorted(df['year'].unique())
                kpi_cols = st.columns(len(years))

                for idx, year in enumerate(years):
                    year_data = df[df['year'] == year].iloc[0]
                    mandated = year_data['mandated_amount']
                    adj_dep = year_data['adjusted_deposits']
                    adj_pay = year_data['adjusted_payments']

                    with kpi_cols[idx]:
                        render_kpi_card(year, mandated, adj_dep, adj_pay)

                st.markdown("---")

                # ─── Detailed Table ───
                st.subheader("📋 جدول تفصیلی به تفکیک سال")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
                    unsafe_allow_html=True
                )

                transfer_out_label = 'انتقال مانده طی اصلاحیه تبصره 2 ماده 5'
                column_labels = {
                    'year': 'سال مالی',
                    'mandated_amount': 'اعتبار تکلیفی',
                    'deposit_amount': 'مجموع واریزی',
                    'payment_amount': 'هزینه کرد',
                    'transfer_in': 'انتقال ورودی',
                    'transfer_out': transfer_out_label,
                    'balance': 'مانده واقعی'
                }
                display_cols = [
                    'year', 'mandated_amount', 'deposit_amount',
                    'payment_amount', 'transfer_in', 'transfer_out', 'balance'
                ]

                df_display = df[display_cols].copy().rename(columns=column_labels)
                df_display[column_labels['year']] = df_display[column_labels['year']].apply(to_persian_numbers)
                for col_key, col_label in column_labels.items():
                    if col_key != 'year':
                        df_display[col_label] = df_display[col_label].apply(to_persian_numbers)

                st.table(df_display)

                # Excel export (no adjusted columns)
                df_excel = df[display_cols].copy().rename(columns=column_labels)
                st.download_button(
                    label="📥 دانلود گزارش به صورت اکسل",
                    data=to_excel(df_excel),
                    file_name=f"financial_report_v2_{selected_code}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                st.markdown("---")

                # ─── Advanced Analytics: Grouped Bar Chart ───
                st.subheader("📊 تحلیل و نمودار")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
                    unsafe_allow_html=True
                )

                chart_data = df.sort_values('year')
                years_persian = [to_persian_numbers(int(y)) for y in chart_data['year']]

                grouped_max_value = max(
                    chart_data['mandated_amount'].max(),
                    chart_data['adjusted_deposits'].max(),
                    chart_data['adjusted_payments'].max(),
                    0
                )
                grouped_tickvals = [grouped_max_value * i / 5 for i in range(6)] if grouped_max_value > 0 else [0]
                grouped_ticktext = [to_persian_numbers(int(v)) for v in grouped_tickvals]

                fig_grouped = go.Figure()

                fig_grouped.add_trace(go.Bar(
                    x=years_persian,
                    y=chart_data['mandated_amount'],
                    name='اعتبار تکلیفی',
                    marker_color='#757575',
                    text=[to_persian_numbers(int(v)) for v in chart_data['mandated_amount']],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=11)
                ))

                fig_grouped.add_trace(go.Bar(
                    x=years_persian,
                    y=chart_data['adjusted_deposits'],
                    name='واریزی تعدیل‌شده',
                    marker_color='#4CAF50',
                    text=[to_persian_numbers(int(v)) for v in chart_data['adjusted_deposits']],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=11)
                ))

                fig_grouped.add_trace(go.Bar(
                    x=years_persian,
                    y=chart_data['adjusted_payments'],
                    name='هزینه تعدیل‌شده',
                    marker_color='#2196F3',
                    text=[to_persian_numbers(int(v)) for v in chart_data['adjusted_payments']],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=11)
                ))

                fig_grouped.update_layout(
                    barmode='group',
                    font=dict(family='Vazirmatn', size=14),
                    title=dict(
                        text='مقایسه اعتبار تکلیفی، واریزی تعدیل‌شده و هزینه تعدیل‌شده',
                        x=0.5,
                        xanchor='center',
                        font=dict(family='Vazirmatn', size=18)
                    ),
                    title_font=dict(family='Vazirmatn'),
                    xaxis=dict(
                        title='سال مالی',
                        tickfont=dict(family='Vazirmatn', size=13),
                        title_font=dict(family='Vazirmatn')
                    ),
                    yaxis=dict(
                        title='مبلغ (میلیون ریال)',
                        tickmode='array',
                        tickvals=grouped_tickvals,
                        ticktext=grouped_ticktext,
                        tickfont=dict(family='Vazirmatn', size=12),
                        title_font=dict(family='Vazirmatn')
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5,
                        font=dict(family='Vazirmatn', size=13)
                    ),
                    legend_font=dict(family='Vazirmatn'),
                    height=600,
                    margin=dict(l=60, r=40, t=80, b=120),
                    plot_bgcolor='#f8f9fa',
                    paper_bgcolor='white'
                )

                st.plotly_chart(fig_grouped, use_container_width=True, theme=None)

                # ─── Cumulative Flow: Waterfall Chart ───
                tot_dep = chart_data['adjusted_deposits'].sum()
                tot_pay = chart_data['adjusted_payments'].sum()
                tot_bal = chart_data['balance'].sum()

                waterfall_labels = [
                    ' واریزی تعدیل‌شده',
                    ' هزینه تعدیل‌شده',
                    ' مانده واقعی'
                ]
                waterfall_values = [tot_dep, -tot_pay, tot_bal]

                waterfall_max_value = max(tot_dep, tot_pay, abs(tot_bal), 0)
                waterfall_tickvals = [waterfall_max_value * i / 5 for i in range(6)] if waterfall_max_value > 0 else [0]
                waterfall_ticktext = [to_persian_numbers(int(v)) for v in waterfall_tickvals]

                fig_waterfall = go.Figure(go.Waterfall(
                    orientation='v',
                    measure=['relative', 'relative', 'total'],
                    x=waterfall_labels,
                    y=waterfall_values,
                    text=[to_persian_numbers(int(v)) for v in waterfall_values],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=12),
                    connector=dict(line=dict(color='#9CA3AF')),
                    increasing=dict(marker=dict(color='#10B981')),
                    decreasing=dict(marker=dict(color='#EF4444')),
                    totals=dict(marker=dict(color='#3B82F6'))
                ))

                fig_waterfall.update_layout(
                    font=dict(family='Vazirmatn', size=14),
                    title=dict(
                        text='نمای تجمعی جریان منابع و مصارف',
                        x=0.5,
                        xanchor='center',
                        font=dict(family='Vazirmatn', size=18)
                    ),
                    title_font=dict(family='Vazirmatn'),
                    xaxis=dict(
                        tickfont=dict(family='Vazirmatn', size=13),
                        title_font=dict(family='Vazirmatn')
                    ),
                    yaxis=dict(
                        title='مبلغ (میلیون ریال)',
                        tickmode='array',
                        tickvals=waterfall_tickvals,
                        ticktext=waterfall_ticktext,
                        tickfont=dict(family='Vazirmatn', size=12),
                        title_font=dict(family='Vazirmatn')
                    ),
                    showlegend=True,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5,
                        font=dict(family='Vazirmatn', size=13)
                    ),
                    height=520,
                    margin=dict(l=60, r=40, t=80, b=120),
                    plot_bgcolor='#f8f9fa',
                    paper_bgcolor='white'
                )

                st.plotly_chart(fig_waterfall, use_container_width=True, theme=None)

    finally:
        db.close()


if __name__ == "__main__":
    main()
