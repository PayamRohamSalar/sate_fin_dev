"""داشبورد عملکرد مشمولین (Employer KPI) — درصد تحقق واریز و شناسایی متخلفان.

Reads directly from the database via ``services.financial_engine``, the same
DB-direct pattern ``dashboard/app.py``'s management dashboards and
``dashboard/views/stagnant_contracts_dashboard.py`` use (read-only analytics,
not a data-entry form — does not need the FastAPI backend running).
"""

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.database import SessionLocal
from services.financial_engine import (
    get_all_employers_financials,
    get_employer_contract_activity,
    get_employer_deposit_performance,
)

DEFAULT_SINCE_JALALI_YEAR = 1402
DEFAULT_RED_THRESHOLD = 50
DEFAULT_YELLOW_THRESHOLD = 80

TIER_ORDER = ["قرمز", "زرد", "سبز", "بدون تکلیف"]
TIER_COLORS = {
    "قرمز": "#EF4444",
    "زرد": "#F59E0B",
    "سبز": "#10B981",
    "بدون تکلیف": "#9CA3AF",
}
TIER_DESCRIPTIONS = {
    "قرمز": "درصد تحقق واریز زیر آستانه بحرانی — دستگاه متخلف، نیازمند پیگیری فوری.",
    "زرد": "درصد تحقق واریز بین دو آستانه — نیازمند پیگیری.",
    "سبز": "درصد تحقق واریز در سطح مطلوب.",
    "بدون تکلیف": "برای بازه انتخاب‌شده، اعتبار تکلیفی ثبت‌شده‌ای برای این مشمول وجود ندارد (نسبت تعریف‌نشده است).",
}

DETAIL_COLUMNS = [
    "employer_name",
    "employer_type",
    "province",
    "mandated_amount",
    "deposit_amount",
    "shortfall_amount",
    "realization_pct",
    "tier",
]
DETAIL_LABELS = {
    "employer_name": "نام مشمول",
    "employer_type": "نوع",
    "province": "استان",
    "mandated_amount": "مجموع اعتبار تکلیفی (ریال)",
    "deposit_amount": "مجموع واریزی (ریال)",
    "shortfall_amount": "کسری واریز (ریال)",
    "realization_pct": "درصد تحقق واریز",
    "tier": "وضعیت",
}
EMPLOYER_TYPE_LABELS = {
    "Mother": "مادر (به همراه زیرمجموعه‌ها)",
    "Subsidiary": "زیرمجموعه",
    "Independent": "مستقل",
}

ACTIVITY_COLUMNS = [
    "employer_name",
    "year",
    "contracts_count",
    "contracts_amount",
    "payments_amount",
]
ACTIVITY_LABELS = {
    "employer_name": "کارفرما",
    "year": "سال (انعقاد قرارداد)",
    "contracts_count": "تعداد قرارداد",
    "contracts_amount": "مبلغ کل قراردادها (ریال)",
    "payments_amount": "پرداختی سال مالی متناظر (ریال)",
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect, .stSlider, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    h1, h2, h3, .stHeadingContainer { text-align: center !important; direction: rtl; }
    table, th, td, .stTable, [data-testid="stTable"] * {
        font-family: 'Vazirmatn', sans-serif !important;
        font-size: 14px !important;
        text-align: center !important;
        direction: rtl !important;
    }
    th { background-color: #f0f2f6 !important; border-bottom: 2px solid #4a4a4a !important; color: black !important; }
    .stPlotlyChart, .js-plotly-plot, .plotly { direction: ltr !important; }
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _to_persian_digits(text) -> str:
    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
    }
    text = str(text)
    for eng, per in persian_digits.items():
        text = text.replace(eng, per)
    return text


def _format_rials(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{value:,.0f}")


def _format_int(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{int(value):,}")


def _format_pct(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{value:,.1f}٪")


@st.cache_data(ttl=120, show_spinner=False)
def _load_all_financials_years():
    """Cached list of fiscal years with any mandate/deposit activity."""
    db = SessionLocal()
    try:
        df = get_all_employers_financials(db)
    finally:
        db.close()
    if df.empty:
        return []
    return sorted(int(y) for y in df["year"].dropna().unique().tolist())


@st.cache_data(ttl=120, show_spinner=False)
def _load_performance(fiscal_years_key, red_threshold, yellow_threshold):
    """Cached load of the deposit-performance table for a tuple of years."""
    db = SessionLocal()
    try:
        df = get_employer_deposit_performance(
            db,
            fiscal_years=list(fiscal_years_key) if fiscal_years_key else None,
            red_threshold=red_threshold,
            yellow_threshold=yellow_threshold,
        )
    finally:
        db.close()
    return df


@st.cache_data(ttl=120, show_spinner=False)
def _load_contract_activity(since_jalali_year):
    """Cached load of per-employer/per-year contract-signing + payment activity."""
    db = SessionLocal()
    try:
        df, meta = get_employer_contract_activity(db, since_jalali_year=since_jalali_year)
    finally:
        db.close()
    return df, meta


st.markdown(
    "<h1 style='text-align: center;'>🚦 داشبورد عملکرد مشمولین</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h4 style='text-align: center; color: gray;'>درصد تحقق واریز (واریزی/تکلیفی) و شناسایی دستگاه‌های متخلف</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

with st.expander("ℹ️ توضیح معیار و سطوح وضعیت", expanded=True):
    st.markdown(
        "این داشبورد **صرفاً نسبت واریزی به تکلیف قانونی** هر مشمول را می‌سنجد "
        "(هزینه‌کرد و مانده حساب در این محاسبه دخیل نیست — برای آن به «داشبورد "
        "اصلی» مراجعه کنید). هر مشمول در یکی از سطوح زیر قرار می‌گیرد:"
    )
    for tier in TIER_ORDER:
        st.markdown(
            f"<div style='margin-bottom:6px;'>"
            f"<span style='display:inline-block; width:10px; height:10px; border-radius:50%; "
            f"background:{TIER_COLORS[tier]}; margin-left:8px;'></span>"
            f"<b>{tier}</b> — {TIER_DESCRIPTIONS[tier]}"
            "</div>",
            unsafe_allow_html=True,
        )
    st.caption(
        "شرکت‌های «مادر» به همراه تمام زیرمجموعه‌هایشان یک ردیف تجمیع‌شده هستند "
        "(همان قاعده تجمیع مالی هلدینگ که در سایر بخش‌های سامانه استفاده می‌شود)."
    )

with st.expander("⚙️ تنظیمات پیشرفته (آستانه‌های وضعیت)"):
    col_a, col_b = st.columns(2)
    with col_a:
        red_threshold = st.slider(
            "سقف درصد برای «قرمز» (زیر این عدد = متخلف):",
            min_value=0, max_value=100, value=DEFAULT_RED_THRESHOLD, step=5,
        )
    with col_b:
        yellow_threshold = st.slider(
            "سقف درصد برای «زرد» (زیر این عدد و بالای قرمز):",
            min_value=int(red_threshold), max_value=100, value=max(DEFAULT_YELLOW_THRESHOLD, int(red_threshold)), step=5,
        )

with st.spinner("در حال بارگذاری سال‌های مالی موجود..."):
    available_years = _load_all_financials_years()

in_scope_years = [y for y in available_years if y >= DEFAULT_SINCE_JALALI_YEAR]

if not in_scope_years:
    st.info(f"هیچ داده مالی از سال {_to_persian_digits(DEFAULT_SINCE_JALALI_YEAR)} به بعد یافت نشد.")
    st.stop()

st.markdown("---")
st.subheader("🔎 انتخاب بازه بررسی")
selected_years = st.multiselect(
    "سال(های) مالی (پیش‌فرض: مجموع همه سال‌ها از ۱۴۰۲) — می‌توانید یک سال را برای نمای سالانه انتخاب کنید:",
    options=in_scope_years,
    default=in_scope_years,
    format_func=lambda y: _to_persian_digits(y),
)

with st.spinner("در حال محاسبه عملکرد مشمولین..."):
    df = _load_performance(tuple(sorted(selected_years)), int(red_threshold), int(yellow_threshold))

if df.empty:
    st.info("هیچ داده‌ای برای بازه انتخاب‌شده یافت نشد.")
    st.stop()

df["employer_type"] = df["employer_type"].map(EMPLOYER_TYPE_LABELS).fillna(df["employer_type"])

st.markdown("---")
st.subheader("🔎 فیلترها")
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    tier_filter = st.multiselect("وضعیت:", options=TIER_ORDER, default=TIER_ORDER)
with filter_col2:
    province_filter = st.multiselect(
        "استان:", options=sorted(df["province"].dropna().unique().tolist())
    )

df_filtered = df[df["tier"].isin(tier_filter)] if tier_filter else df.iloc[0:0]
if province_filter:
    df_filtered = df_filtered[df_filtered["province"].isin(province_filter)]

st.markdown("---")
st.subheader("🔑 شاخص‌های کلیدی")
kpi_cols = st.columns(4)
tier_counts = df["tier"].value_counts()
for idx, tier in enumerate(TIER_ORDER):
    count = int(tier_counts.get(tier, 0))
    with kpi_cols[idx]:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #e5e7eb; border-right: 5px solid {TIER_COLORS[tier]};
                        border-radius: 8px; padding: 16px; text-align: center;
                        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                <div style="font-size: 14px; color: #6b7280;">{tier}</div>
                <div style="font-size: 28px; font-weight: 700; color: #111827;">{_format_int(count)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

red_shortfall_total = df.loc[df["tier"] == "قرمز", "shortfall_amount"].sum()
st.markdown(
    f"""
    <div style="margin-top: 14px; background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px;
                padding: 14px; text-align: center;">
        <span style="color:#991B1B; font-weight:600;">💰 مجموع کسری واریز مشمولین قرمز: </span>
        <span style="color:#991B1B; font-weight:700; font-size: 18px;">{_format_rials(red_shortfall_total)} ریال</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")
st.subheader("📊 رتبه‌بندی مشمولین بر اساس درصد تحقق واریز")
chart_df = df[df["tier"] != "بدون تکلیف"].copy()
chart_df = chart_df.sort_values("realization_pct", ascending=True).head(20)
if chart_df.empty:
    st.info("داده‌ای برای رسم نمودار (با تکلیف تعریف‌شده) یافت نشد.")
else:
    fig = go.Figure(
        go.Bar(
            x=chart_df["realization_pct"],
            y=chart_df["employer_name"],
            orientation="h",
            marker_color=[TIER_COLORS[t] for t in chart_df["tier"]],
            text=[_to_persian_digits(f"{v:,.1f}٪") for v in chart_df["realization_pct"]],
            textposition="auto",
        )
    )
    fig.update_layout(
        font=dict(family="Vazirmatn", size=14),
        xaxis=dict(title="درصد تحقق واریز", tickfont=dict(family="Vazirmatn")),
        yaxis=dict(title="", autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
        height=max(320, 24 * len(chart_df)),
        margin=dict(l=20, r=20, t=20, b=40),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        showlegend=False,
    )
    st.caption("۲۰ مشمول با کمترین درصد تحقق واریز (از میان مشمولینی که تکلیف تعریف‌شده دارند)")
    st.plotly_chart(fig, width="stretch", theme=None)

st.markdown("---")
st.subheader("📋 فهرست تفصیلی مشمولین")
st.caption(f"{_format_int(len(df_filtered))} مشمول مطابق فیلترهای انتخاب‌شده")

tier_priority = {t: i for i, t in enumerate(TIER_ORDER)}
df_sorted = df_filtered.copy()
df_sorted["_tier_priority"] = df_sorted["tier"].map(tier_priority)
df_sorted = df_sorted.sort_values(
    by=["_tier_priority", "realization_pct"],
    ascending=[True, True],
    na_position="last",
)

df_display = df_sorted[DETAIL_COLUMNS].rename(columns=DETAIL_LABELS)
for col_key in ("mandated_amount", "deposit_amount", "shortfall_amount"):
    df_display[DETAIL_LABELS[col_key]] = df_sorted[col_key].apply(_format_rials)
df_display[DETAIL_LABELS["realization_pct"]] = df_sorted["realization_pct"].apply(_format_pct)

if df_display.empty:
    st.info("با فیلترهای فعلی هیچ مشمولی یافت نشد.")
else:
    st.table(df_display)

st.markdown("---")


def _to_excel(export_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Employer KPI")
    output.seek(0)
    return output.getvalue()


export_df = df_sorted[DETAIL_COLUMNS].rename(columns=DETAIL_LABELS)
years_label = "-".join(str(y) for y in sorted(selected_years)) if selected_years else "all"
st.download_button(
    label="📥 دانلود فهرست کامل به صورت اکسل",
    data=_to_excel(export_df),
    file_name=f"employer_kpi_{years_label}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")
st.subheader("📑 فعالیت قراردادی و پرداختی مشمولین (به تفکیک سال)")
st.caption(
    "تعداد و مبلغ قراردادها بر اساس **سال انعقاد** (تاریخ قرارداد) محاسبه شده؛ "
    "مبلغ پرداختی بر اساس **سال مالی تأمین اعتبار** (همان قاعده‌ای که در سایر "
    "بخش‌های سامانه استفاده می‌شود) است و لزوماً مربوط به قراردادهای همان سال "
    "نیست — چون پرداخت یک قرارداد می‌تواند در سال‌های بعد از انعقاد آن انجام "
    "شود. به همین دلیل عمداً «درصد پرداخت‌شده» بین این دو مبلغ محاسبه نشده است."
)

with st.spinner("در حال بارگذاری فعالیت قراردادی..."):
    df_activity, activity_meta = _load_contract_activity(int(DEFAULT_SINCE_JALALI_YEAR))

if activity_meta["excluded_no_contract_date"] > 0:
    st.warning(
        f"⚠️ {_format_int(activity_meta['excluded_no_contract_date'])} قرارداد فاقد "
        "تاریخ ثبت‌شده هستند و از شمارش/مبلغ قراردادها کنار گذاشته شدند."
    )
if activity_meta["excluded_no_funding_year"] > 0:
    st.warning(
        f"⚠️ {_format_int(activity_meta['excluded_no_funding_year'])} پرداخت فاقد "
        "سال مالی معتبر هستند و از مبلغ پرداختی کنار گذاشته شدند."
    )

if df_activity.empty:
    st.info(f"هیچ فعالیت قراردادی/پرداختی از سال {_to_persian_digits(DEFAULT_SINCE_JALALI_YEAR)} به بعد یافت نشد.")
else:
    activity_years = sorted(df_activity["year"].unique().tolist())
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        activity_employer_filter = st.multiselect(
            "کارفرما (خالی = همه):",
            options=sorted(df_activity["employer_name"].unique().tolist()),
            key="activity_employer_filter",
        )
    with act_col2:
        activity_year_filter = st.multiselect(
            "سال:",
            options=activity_years,
            default=activity_years,
            format_func=lambda y: _to_persian_digits(y),
            key="activity_year_filter",
        )

    df_act_filtered = (
        df_activity[df_activity["year"].isin(activity_year_filter)]
        if activity_year_filter
        else df_activity.iloc[0:0]
    )
    if activity_employer_filter:
        df_act_filtered = df_act_filtered[
            df_act_filtered["employer_name"].isin(activity_employer_filter)
        ]
    df_act_filtered = df_act_filtered.sort_values(["employer_name", "year"])

    st.caption(f"{_format_int(len(df_act_filtered))} ردیف (کارفرما × سال) مطابق فیلترهای انتخاب‌شده")

    act_display = df_act_filtered[ACTIVITY_COLUMNS].rename(columns=ACTIVITY_LABELS)
    act_display[ACTIVITY_LABELS["year"]] = df_act_filtered["year"].apply(_format_int)
    act_display[ACTIVITY_LABELS["contracts_count"]] = df_act_filtered["contracts_count"].apply(_format_int)
    act_display[ACTIVITY_LABELS["contracts_amount"]] = df_act_filtered["contracts_amount"].apply(_format_rials)
    act_display[ACTIVITY_LABELS["payments_amount"]] = df_act_filtered["payments_amount"].apply(_format_rials)

    if act_display.empty:
        st.info("با فیلترهای فعلی داده‌ای یافت نشد.")
    else:
        st.table(act_display)

    act_export_df = df_act_filtered[ACTIVITY_COLUMNS].rename(columns=ACTIVITY_LABELS)
    st.download_button(
        label="📥 دانلود فعالیت قراردادی/پرداختی (اکسل)",
        data=_to_excel(act_export_df),
        file_name="employer_contract_activity.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="activity_download_button",
    )
