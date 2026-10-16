import io
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.contract import Contract
from models.deposits import AnnualMandate, DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.transfer import CreditTransfer
from fund_balance_tab import render_fund_balance_tab
from services.financial_engine import (
    calculate_balance_1405,
    calculate_combined_pool_balance,
    get_all_employers_financials,
)

FINANCIAL_COLUMNS = [
    "mandated_amount",
    "deposit_amount",
    "payment_amount",
    "transfer_in",
    "transfer_out",
    "balance",
]

TRANSFER_OUT_LABEL = "انتقال مانده طی اصلاحیه تبصره 2 ماده 5"
COLUMN_LABELS = {
    "year": "سال مالی",
    "mandated_amount": "اعتبار تکلیفی",
    "deposit_amount": "مجموع واریزی",
    "payment_amount": "هزینه کرد",
    "transfer_in": "انتقال ورودی",
    "transfer_out": TRANSFER_OUT_LABEL,
    "balance": "مانده واقعی",
}
DISPLAY_COLUMNS = [
    "year",
    "mandated_amount",
    "deposit_amount",
    "payment_amount",
    "transfer_in",
    "transfer_out",
    "balance",
]


def get_employer_financials(db: Session, employer_code: str):
    """Fetch and aggregate financial data for a specific employer across all years."""
    employer = db.query(Employer).filter(Employer.classification_code == employer_code).first()
    if not employer:
        return pd.DataFrame()

    if employer.employer_type == "Mother":
        codes_to_include = [employer_code]
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer_code,
            Employer.is_deleted == False,
        ).all()
        codes_to_include.extend([s[0] for s in subsidiaries])
    else:
        codes_to_include = [employer_code]

    mandates_query = db.query(
        AnnualMandate.fiscal_year.label("year"),
        func.sum(AnnualMandate.mandated_amount).label("mandated_amount"),
    ).filter(
        AnnualMandate.employer_code.in_(codes_to_include),
        AnnualMandate.is_deleted == False,
    ).group_by(AnnualMandate.fiscal_year)
    df_mandates = pd.read_sql(mandates_query.statement, db.bind)

    deposits_query = db.query(
        DepositReceipt.fiscal_year.label("year"),
        func.sum(DepositReceipt.deposit_amount).label("deposit_amount"),
    ).filter(
        DepositReceipt.employer_code.in_(codes_to_include),
        DepositReceipt.is_deleted == False,
    ).group_by(DepositReceipt.fiscal_year)
    df_deposits = pd.read_sql(deposits_query.statement, db.bind)

    payments_query = db.query(
        Payment.funding_year.label("year"),
        func.sum(Payment.amount).label("payment_amount"),
    ).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code.in_(codes_to_include),
        Payment.is_deleted == False,
        Contract.is_deleted == False,
    ).group_by(Payment.funding_year)
    df_payments = pd.read_sql(payments_query.statement, db.bind)

    transfers_in_query = db.query(
        CreditTransfer.fiscal_year.label("year"),
        func.sum(CreditTransfer.amount).label("transfer_in"),
    ).filter(
        CreditTransfer.destination_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False,
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_in = pd.read_sql(transfers_in_query.statement, db.bind)

    transfers_out_query = db.query(
        CreditTransfer.fiscal_year.label("year"),
        func.sum(CreditTransfer.amount).label("transfer_out"),
    ).filter(
        CreditTransfer.source_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False,
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_out = pd.read_sql(transfers_out_query.statement, db.bind)

    dfs = [df_mandates, df_deposits, df_payments, df_transfers_in, df_transfers_out]
    df_merged = dfs[0]
    for df in dfs[1:]:
        df_merged = df_merged.merge(df, on="year", how="outer")
    df_merged = df_merged.fillna(0)

    df_merged["balance"] = (
        df_merged["deposit_amount"]
        + df_merged["transfer_in"]
        - df_merged["payment_amount"]
        - df_merged["transfer_out"]
    )
    df_merged = df_merged.sort_values("year")
    return df_merged


def render_kpi_card(year, mandated, adj_dep, adj_pay):
    """Render a styled HTML KPI card for a single fiscal year."""
    dep_pct = min(100, (adj_dep / mandated * 100) if mandated > 0 else 0)
    pay_pct = min(100, (adj_pay / mandated * 100) if mandated > 0 else 0)

    html_content = f"""
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
    """
    st.markdown(html_content, unsafe_allow_html=True)


def to_persian_numbers(text):
    """Convert English digits to Persian digits and format numbers with thousand separators."""
    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
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
    return db.query(Employer).filter(
        Employer.status == "Active",
        Employer.is_deleted == False,
    ).order_by(Employer.name).all()


def to_excel(df: pd.DataFrame) -> bytes:
    """Convert dataframe to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Financial Report")
    output.seek(0)
    return output.getvalue()


def add_adjusted_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["adjusted_deposits"] = df["deposit_amount"] + df["transfer_in"]
    df["adjusted_payments"] = df["payment_amount"] + df["transfer_out"]
    return df


def convert_financials_to_millions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    existing_financial_cols = [col for col in FINANCIAL_COLUMNS if col in df.columns]
    df[existing_financial_cols] = df[existing_financial_cols] / 1_000_000
    return df


def million_rials_label():
    st.markdown(
        "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
        unsafe_allow_html=True,
    )


def persian_tick_values(values, steps=5):
    values = pd.Series(values).dropna()
    if values.empty:
        return [0], ["۰"]

    min_value = min(0, float(values.min()))
    max_value = max(0, float(values.max()))
    if min_value == max_value:
        return [0], ["۰"]

    tickvals = [min_value + (max_value - min_value) * i / steps for i in range(steps + 1)]
    ticktext = [to_persian_numbers(int(v)) for v in tickvals]
    return tickvals, ticktext


def render_yearly_kpi_cards(df: pd.DataFrame):
    years = sorted(df["year"].unique())
    kpi_cols = st.columns(len(years))

    for idx, year in enumerate(years):
        year_data = df[df["year"] == year].iloc[0]
        with kpi_cols[idx]:
            render_kpi_card(
                year,
                year_data["mandated_amount"],
                year_data["adjusted_deposits"],
                year_data["adjusted_payments"],
            )


def render_grouped_bar_chart(chart_data: pd.DataFrame):
    chart_data = chart_data.sort_values("year")
    years_persian = [to_persian_numbers(int(y)) for y in chart_data["year"]]
    tickvals, ticktext = persian_tick_values(pd.concat([
        chart_data["mandated_amount"],
        chart_data["adjusted_deposits"],
        chart_data["adjusted_payments"],
    ]))

    fig_grouped = go.Figure()
    fig_grouped.add_trace(go.Bar(
        x=years_persian,
        y=chart_data["mandated_amount"],
        name="اعتبار تکلیفی",
        marker_color="#757575",
        text=[to_persian_numbers(int(v)) for v in chart_data["mandated_amount"]],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_grouped.add_trace(go.Bar(
        x=years_persian,
        y=chart_data["adjusted_deposits"],
        name="واریزی تعدیل‌شده",
        marker_color="#4CAF50",
        text=[to_persian_numbers(int(v)) for v in chart_data["adjusted_deposits"]],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_grouped.add_trace(go.Bar(
        x=years_persian,
        y=chart_data["adjusted_payments"],
        name="هزینه تعدیل‌شده",
        marker_color="#2196F3",
        text=[to_persian_numbers(int(v)) for v in chart_data["adjusted_payments"]],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_grouped.update_layout(
        barmode="group",
        font=dict(family="Vazirmatn", size=14),
        title=dict(
            text="مقایسه اعتبار تکلیفی، واریزی تعدیل‌شده و هزینه تعدیل‌شده",
            x=0.5,
            xanchor="center",
            font=dict(family="Vazirmatn", size=18),
        ),
        title_font=dict(family="Vazirmatn"),
        xaxis=dict(
            title="سال مالی",
            tickfont=dict(family="Vazirmatn", size=13),
            title_font=dict(family="Vazirmatn"),
        ),
        yaxis=dict(
            title="مبلغ (میلیون ریال)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(family="Vazirmatn", size=12),
            title_font=dict(family="Vazirmatn"),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Vazirmatn", size=13),
        ),
        legend_font=dict(family="Vazirmatn"),
        height=600,
        margin=dict(l=60, r=40, t=80, b=120),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_grouped, width="stretch", theme=None)


def render_waterfall_chart(chart_data: pd.DataFrame):
    tot_dep = chart_data["adjusted_deposits"].sum()
    tot_pay = chart_data["adjusted_payments"].sum()
    tot_bal = chart_data["balance"].sum()

    waterfall_labels = [" واریزی تعدیل‌شده", " هزینه تعدیل‌شده", " مانده واقعی"]
    waterfall_values = [tot_dep, -tot_pay, tot_bal]
    cumulative_values = [0, tot_dep, tot_dep - tot_pay, tot_bal]
    tickvals, ticktext = persian_tick_values(cumulative_values)

    fig_waterfall = go.Figure(go.Waterfall(
        name="جریان منابع و مصارف",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=waterfall_labels,
        y=waterfall_values,
        text=[to_persian_numbers(int(v)) for v in waterfall_values],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=12),
        connector=dict(line=dict(color="#9CA3AF")),
        increasing=dict(marker=dict(color="#10B981")),
        decreasing=dict(marker=dict(color="#EF4444")),
        totals=dict(marker=dict(color="#3B82F6")),
    ))
    fig_waterfall.update_layout(
        font=dict(family="Vazirmatn", size=14),
        title=dict(
            text="نمای تجمعی جریان منابع و مصارف",
            x=0.5,
            xanchor="center",
            font=dict(family="Vazirmatn", size=18),
        ),
        title_font=dict(family="Vazirmatn"),
        xaxis=dict(
            tickfont=dict(family="Vazirmatn", size=13),
            title_font=dict(family="Vazirmatn"),
        ),
        yaxis=dict(
            title="مبلغ (میلیون ریال)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(family="Vazirmatn", size=12),
            title_font=dict(family="Vazirmatn"),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Vazirmatn", size=13),
        ),
        height=520,
        margin=dict(l=60, r=40, t=80, b=120),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_waterfall, width="stretch", theme=None)


def render_detailed_table_and_download(df: pd.DataFrame, file_name: str):
    st.subheader("📋 جدول تفصیلی به تفکیک سال")
    million_rials_label()

    df_display = df[DISPLAY_COLUMNS].copy().rename(columns=COLUMN_LABELS)
    df_display[COLUMN_LABELS["year"]] = df_display[COLUMN_LABELS["year"]].apply(to_persian_numbers)
    for col_key, col_label in COLUMN_LABELS.items():
        if col_key != "year":
            df_display[col_label] = df_display[col_label].apply(to_persian_numbers)

    st.table(df_display)

    df_excel = df[DISPLAY_COLUMNS].copy().rename(columns=COLUMN_LABELS)
    st.download_button(
        label="📥 دانلود گزارش به صورت اکسل",
        data=to_excel(df_excel),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_tab1(db: Session, employers):
    employer_options = {emp.classification_code: f"{emp.name} ({emp.classification_code})" for emp in employers}
    employer_keys = list(employer_options.keys())
    default_index = employer_keys.index("231500") if "231500" in employer_keys else 0

    selected_code = st.selectbox(
        "انتخاب مشمول:",
        options=employer_keys,
        format_func=lambda x: employer_options[x],
        index=default_index,
    )

    if not selected_code:
        return

    selected_employer = next(emp for emp in employers if emp.classification_code == selected_code)

    st.subheader(f"اطلاعات مشمول: {selected_employer.name}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**کد طبقه‌بندی:** {selected_employer.classification_code}")
    with col2:
        st.info(f"**استان:** {selected_employer.province}")
    with col3:
        st.info(f"**سازمان بالادست:** {selected_employer.upper_organization}")

    st.markdown("---")

    with st.spinner("در حال بارگذاری اطلاعات مالی..."):
        df = get_employer_financials(db, selected_code)

    df = df[df["year"] >= 1402]
    if df.empty:
        st.warning("هیچ داده مالی برای این مشمول از سال ۱۴۰۲ به بعد یافت نشد.")
        return

    df = add_adjusted_columns(convert_financials_to_millions(df))

    # Combined 1402+1404 pool balance (2026-09-16, at Payam's request):
    # credit transfers are no longer netted into a single year's balance
    # (see calculate_combined_pool_balance's docstring for why -- a data
    # error in one year's figures could make a legitimate transfer look
    # like it overdrew that year alone). Shown here alongside the existing
    # per-year cards, which are unchanged.
    # 1405 credit is its own balance: by law it cannot be transferred, so it
    # is shown beside (never inside) the transferable 1402+1404 pool.
    combined_balance = calculate_combined_pool_balance(db, selected_code)
    balance_1405 = calculate_balance_1405(db, selected_code)
    pool_col, current_col = st.columns(2)
    pool_col.metric(
        "💰 مانده تجمیعی ۱۴۰۲+۱۴۰۴ (پس از انتقال اعتبار)",
        f"{combined_balance / 1_000_000:,.0f} میلیون ریال",
        help="واریزی منهای هزینه هر دو سال، به‌علاوهٔ خالص انتقال اعتبار ورودی/خروجی این مشمول -- انتقال اعتبار از محل مجموع این دو سال کسر می‌شود، نه یک سال مشخص.",
    )
    current_col.metric(
        "🔒 مانده ۱۴۰۵ (غیرقابل انتقال)",
        f"{balance_1405 / 1_000_000:,.0f} میلیون ریال",
        help="واریزی ۱۴۰۵ منهای پرداخت‌هایی که سال مالی آن‌ها ۱۴۰۵ ثبت شده است. اعتبار سال جاری را نمی‌توان انتقال داد.",
    )

    st.subheader("🔑 شاخص‌های کلیدی")
    million_rials_label()
    render_yearly_kpi_cards(df)

    st.markdown("---")
    render_detailed_table_and_download(df, f"financial_report_v2_{selected_code}.xlsx")

    st.markdown("---")
    st.subheader("📊 تحلیل و نمودار")
    million_rials_label()
    render_grouped_bar_chart(df)
    render_waterfall_chart(df)


def render_top10_employers_chart(df_all: pd.DataFrame):
    st.markdown("### 📊 ۱۰ مشمول برتر بر اساس میزان واریزی")

    top10 = df_all.groupby(
        ["employer_code", "employer_name"], as_index=False
    )["deposit_amount"].sum().nlargest(10, "deposit_amount")

    tickvals, ticktext = persian_tick_values(top10["deposit_amount"])
    fig_top10 = go.Figure(go.Bar(
        x=top10["deposit_amount"],
        y=top10["employer_name"],
        orientation="h",
        text=top10["deposit_amount"].apply(lambda v: to_persian_numbers(int(v))),
        textposition="auto",
        marker_color="#2196F3",
        name="مجموع واریزی",
    ))
    fig_top10.update_layout(
        font=dict(family="Vazirmatn", size=14),
        xaxis=dict(
            title="مبلغ واریزی (میلیون ریال)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(family="Vazirmatn", size=12),
            title_font=dict(family="Vazirmatn"),
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            tickfont=dict(family="Vazirmatn", size=12),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Vazirmatn", size=13),
        ),
        height=500,
        margin=dict(l=20, r=20, t=40, b=100),
    )
    st.plotly_chart(fig_top10, width="stretch", theme=None)


def render_global_excel_download(df_all: pd.DataFrame):
    df_export = df_all.copy().rename(columns={
        "employer_code": "کد مشمول",
        "employer_name": "نام مشمول",
        "year": "سال مالی",
        "mandated_amount": "اعتبار تکلیفی",
        "deposit_amount": "مجموع واریزی",
        "payment_amount": "هزینه کرد",
        "transfer_in": "انتقال ورودی",
        "transfer_out": "انتقال خروجی",
        "balance": "مانده واقعی",
    })

    st.download_button(
        label="📥 دانلود گزارش جامع کل مشمولین (اکسل)",
        data=to_excel(df_export),
        file_name="financial_report_all_employers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_tab2(db: Session):
    st.subheader("🏢 نمای کلان - خلاصه مدیریتی")

    with st.spinner("در حال بارگذاری اطلاعات کلان..."):
        df_all = get_all_employers_financials(db)

    if df_all.empty:
        st.warning("هیچ داده مالی در سیستم یافت نشد.")
        return

    df_all = df_all[df_all["year"] >= 1402]
    if df_all.empty:
        st.warning("هیچ داده مالی از سال ۱۴۰۲ به بعد یافت نشد.")
        return

    df_all = convert_financials_to_millions(df_all)
    df_macro_yearly = df_all.groupby("year", as_index=False)[FINANCIAL_COLUMNS].sum()
    df_macro_yearly = add_adjusted_columns(df_macro_yearly)

    st.subheader("🔑 شاخص‌های کلیدی")
    million_rials_label()
    render_yearly_kpi_cards(df_macro_yearly)

    st.markdown("---")
    st.subheader("📊 تحلیل و نمودار")
    million_rials_label()
    render_grouped_bar_chart(df_macro_yearly)
    render_waterfall_chart(df_macro_yearly)

    st.markdown("---")
    render_top10_employers_chart(df_all)

    st.markdown("---")
    render_global_excel_download(df_all)


def render_dashboard():
    """Render the main management dashboard (used as a st.Page target)."""
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

        tab1, tab2, tab3 = st.tabs([
            "ترازنامه مشمولین",
            "نمای کلان - Executive Summary",
            "ترازنامه دبیرخانه و صندوق",
        ])
        with tab1:
            render_tab1(db, employers)
        with tab2:
            render_tab2(db)
        with tab3:
            render_fund_balance_tab(db)
    finally:
        db.close()


def _inject_global_css():
    """Global CSS: aggressive RTL override for Streamlit internal containers."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    /* Force RTL on main containers and text inputs */
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    /* Fix sidebar text alignment */
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 1. MUST be the first Streamlit command executed in the file.
    st.set_page_config(page_title="سامانه مالی ساتع", layout="wide")

    # 2. Define the pages via the st.Page API.
    dash_page = st.Page(render_dashboard, title="داشبورد اصلی", icon="📊", default=True)
    stagnant_contracts_page = st.Page(
        "views/stagnant_contracts_dashboard.py",
        title="وضعیت قراردادهای ثبت شده",
        icon="🕒",
    )
    employer_kpi_page = st.Page(
        "views/employer_kpi_dashboard.py",
        title="عملکرد مشمولین",
        icon="🚦",
    )
    university_ranking_page = st.Page(
        "views/university_ranking_dashboard.py",
        title="رتبه‌بندی دانشگاه‌ها",
        icon="🎓",
    )
    researcher_ranking_page = st.Page(
        "views/researcher_ranking_dashboard.py",
        title="رتبه‌بندی پژوهشگران",
        icon="🧑‍🔬",
    )
    demand_proposal_page = st.Page(
        "views/demand_proposal_dashboard.py",
        title="تقاضا و پیشنهاده",
        icon="📮",
    )
    holding_group_page = st.Page(
        "views/holding_group_dashboard.py",
        title="عملکرد گروه‌های سازمانی",
        icon="🏢",
    )
    batch_payments_page = st.Page("views/batch_payments_page.py", title="ثبت دسته‌ای پرداخت", icon="📝")
    contract_entry_page = st.Page("views/contract_entry_page.py", title="ثبت قرارداد جدید", icon="📄")
    contract_edit_page = st.Page("views/contract_edit_page.py", title="جستجو و ویرایش قرارداد", icon="✏️")
    university_entry_page = st.Page("views/university_entry_page.py", title="ثبت موسسه مجری", icon="🏫")
    researcher_entry_page = st.Page("views/researcher_entry_page.py", title="ثبت اطلاعات فناور", icon="🧑‍🔬")
    deposit_entry_page = st.Page("views/deposit_entry_page.py", title="ثبت واریزی شرکت‌ها", icon="💰")
    trustee_payment_entry_page = st.Page(
        "views/trustee_payment_entry_page.py", title="ثبت پرداخت‌های امانی", icon="🏦"
    )
    credit_transfer_page = st.Page(
        "views/credit_transfer_page.py", title="مدیریت انتقال اعتبار", icon="🔄"
    )

    # 3. Group and initialize navigation.
    pg = st.navigation({
        "داشبوردهای مدیریتی": [
            dash_page, stagnant_contracts_page, employer_kpi_page,
            university_ranking_page, researcher_ranking_page, demand_proposal_page,
            holding_group_page,
        ],
        "فرم‌های ورود اطلاعات": [
            batch_payments_page,
            contract_entry_page,
            contract_edit_page,
            university_entry_page,
            researcher_entry_page,
            deposit_entry_page,
            trustee_payment_entry_page,
            credit_transfer_page,
        ],
    })

    # 4. Inject global CSS (RTL & Fonts) before rendering the active page.
    _inject_global_css()

    # 5. CRITICAL: Execute the navigation / render the active page.
    pg.run()


if __name__ == "__main__":
    main()
