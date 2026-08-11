"""داشبورد وضعیت قراردادهای ثبت شده — وضعیت فعالیت قراردادهای منعقد شده از ۱۴۰۲.

Reads directly from the database via ``services.financial_engine``, the same
pattern ``dashboard/app.py``'s management-dashboard tabs use (this is an
analytical/read-only view, not a data-entry form, so it does not go through
the FastAPI layer). See Docs/SATE_Living_Documentation.md §4.1 and the
``get_contract_status_overview`` docstring for why this dashboard's dormancy
measure (elapsed calendar days since the last ``payment_date``, falling back
to ``notification_date`` when ``payment_date`` is unset, and combined with
any ``trustee_payments`` attributed to the contract) is a deliberately
different question from the funding-year-based status used by
``services.financial_engine.get_contracts_with_dynamic_status``.
"""

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.database import SessionLocal
from core.date_helper import format_jalali
from services.financial_engine import get_contract_status_overview

DEFAULT_SINCE_JALALI_YEAR = 1402
DEFAULT_DORMANT_DAYS_THRESHOLD = 365

STATUS_ORDER = ["راکد", "آغاز نشده", "فعال", "خاتمه‌یافته"]
STATUS_COLORS = {
    "راکد": "#EF4444",
    "آغاز نشده": "#F59E0B",
    "فعال": "#10B981",
    "خاتمه‌یافته": "#3B82F6",
}
STATUS_DESCRIPTIONS = {
    "خاتمه‌یافته": "مجموع پرداختی‌های ثبت‌شده، کل مبلغ قرارداد را پوشش داده است.",
    "آغاز نشده": "از زمان انعقاد تاکنون هیچ پرداختی به این قرارداد ثبت نشده است.",
    "راکد": "قرارداد پرداختی داشته اما بیش از آستانه رکود (پیش‌فرض یک سال / ۳۶۵ روز) است پرداخت جدیدی ثبت نشده — مشمول بررسی برای اصلاحیه تبصره ۲ ماده ۵.",
    "فعال": "قرارداد خاتمه نیافته و در بازه آستانه رکود اخیر (پیش‌فرض ۳۶۵ روز) پرداختی به آن صورت گرفته است.",
}

DETAIL_COLUMNS = [
    "tracking_code",
    "title",
    "employer_name",
    "university_name",
    "contract_jalali_year",
    "total_amount",
    "total_paid",
    "trustee_paid_amount",
    "remaining_amount",
    "last_payment_date_jalali",
    "days_since_last_payment",
    "status",
    "data_quality_flag",
]
DETAIL_LABELS = {
    "tracking_code": "کد رهگیری قرارداد",
    "title": "عنوان قرارداد",
    "employer_name": "کارفرما (مشمول)",
    "university_name": "دانشگاه / موسسه مجری",
    "contract_jalali_year": "سال انعقاد",
    "total_amount": "مبلغ کل قرارداد (ریال)",
    "total_paid": "مبلغ دریافتی (ریال)",
    "trustee_paid_amount": "از این مبلغ، پرداخت امانی (ریال)",
    "remaining_amount": "مانده باقی‌مانده (ریال)",
    "last_payment_date_jalali": "تاریخ آخرین پرداخت",
    "days_since_last_payment": "روز از آخرین پرداخت",
    "status": "وضعیت",
    "data_quality_flag": "یادداشت کیفیت داده",
}
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect, p, div {
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
    """Convert English digits in ``text`` to Persian digits."""
    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
    }
    text = str(text)
    for eng, per in persian_digits.items():
        text = text.replace(eng, per)
    return text


def _format_rials(value) -> str:
    """Format a numeric Rial amount as a comma-grouped Persian-digit string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{value:,.0f}")


def _format_int(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{int(value):,}")


def _format_text(value) -> str:
    """Format an optional free-text cell (e.g. the data-quality note)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return str(value)


@st.cache_data(ttl=120, show_spinner=False)
def _load_overview(since_jalali_year: int, dormant_days_threshold: int):
    """Cached load of the contract status overview (2-minute TTL).

    Returns plain-serializable pieces (DataFrame + dict) since Streamlit's
    cache cannot key on a live DB session; a fresh ``SessionLocal`` is opened
    and closed on every cache miss.
    """
    db = SessionLocal()
    try:
        df, meta = get_contract_status_overview(
            db,
            since_jalali_year=since_jalali_year,
            dormant_days_threshold=dormant_days_threshold,
        )
    finally:
        db.close()
    return df, meta


st.markdown(
    "<h1 style='text-align: center;'>🕒 وضعیت قراردادهای ثبت شده</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h4 style='text-align: center; color: gray;'>وضعیت فعالیت قراردادهای منعقد شده از سال ۱۴۰۲ به بعد</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

with st.expander("ℹ️ توضیح دامنه بررسی و تعریف وضعیت‌ها", expanded=True):
    st.markdown(
        "در این داشبورد **صرفاً قراردادهای منعقد شده از سال ۱۴۰۲ به بعد** "
        "(بر اساس تاریخ قرارداد) بررسی می‌شوند. هر قرارداد در یکی از چهار "
        "وضعیت زیر قرار می‌گیرد:"
    )
    for status in STATUS_ORDER:
        st.markdown(
            f"<div style='margin-bottom:6px;'>"
            f"<span style='display:inline-block; width:10px; height:10px; border-radius:50%; "
            f"background:{STATUS_COLORS[status]}; margin-left:8px;'></span>"
            f"<b>{status}</b> — {STATUS_DESCRIPTIONS[status]}"
            "</div>",
            unsafe_allow_html=True,
        )
    st.caption(
        "معیار «راکد بودن» بر اساس تاریخ واقعی پرداخت (payment_date) محاسبه می‌شود و در "
        "صورت نبود آن، از تاریخ ابلاغ (notification_date) همان پرداخت استفاده می‌شود؛ "
        "این سنجه با سال مالی تأمین اعتبار (funding_year) یکی نیست — چون فاصله واقعی "
        "زمانی از آخرین جریان نقدی/ابلاغ را می‌سنجد، نه سال بودجه."
    )
    st.caption(
        "«مبلغ دریافتی» و «تاریخ آخرین پرداخت» علاوه بر پرداخت‌های ثبت‌شده در جدول اصلی "
        "پرداخت‌ها، پرداخت‌های «امانی» (خارج از منابع کارفرما، از محل منابع موسسه مجری) "
        "مرتبط با آن قرارداد را نیز لحاظ می‌کنند — چون از منظر قرارداد، این وجوه هم واقعاً "
        "دریافت شده‌اند. این پرداخت‌ها هرگز از اعتبار/مانده کارفرمایان کسر نمی‌شوند؛ فقط "
        "برای تعیین وضعیت قرارداد استفاده می‌شوند."
    )

with st.expander("⚙️ تنظیمات پیشرفته (در صورت نیاز به تغییر مفروضات پیش‌فرض)"):
    col_a, col_b = st.columns(2)
    with col_a:
        since_year = st.number_input(
            "بررسی قراردادهای منعقد شده از سال:",
            min_value=1380,
            max_value=1420,
            value=DEFAULT_SINCE_JALALI_YEAR,
            step=1,
        )
    with col_b:
        dormant_days = st.number_input(
            "آستانه رکود (روز از آخرین پرداخت):",
            min_value=30,
            max_value=1825,
            value=DEFAULT_DORMANT_DAYS_THRESHOLD,
            step=30,
        )

with st.spinner("در حال بارگذاری اطلاعات قراردادها..."):
    df, meta = _load_overview(int(since_year), int(dormant_days))

if meta["excluded_no_contract_date"] > 0:
    st.warning(
        f"⚠️ {_format_int(meta['excluded_no_contract_date'])} قرارداد فاقد "
        "تاریخ ثبت‌شده (contract_date) هستند و چون سال انعقادشان قابل تعیین "
        "نیست، از این تحلیل کنار گذاشته شدند."
    )
if meta["missing_payment_date_flags"] > 0:
    st.warning(
        f"⚠️ {_format_int(meta['missing_payment_date_flags'])} قرارداد پرداخت "
        "ثبت‌شده دارند اما تاریخ پرداخت آن‌ها نامعتبر/خالی است؛ این موارد به "
        "صورت محافظه‌کارانه «راکد» درنظر گرفته شده‌اند (ستون یادداشت کیفیت "
        "داده را در جدول ببینید)."
    )
if meta["contracts_with_trustee_payment"] > 0:
    st.info(
        f"ℹ️ {_format_int(meta['contracts_with_trustee_payment'])} قرارداد دارای "
        "پرداخت «امانی» (خارج از منابع کارفرما) هستند؛ مبلغ و تاریخ آن در مبلغ "
        "دریافتی، تاریخ آخرین پرداخت و وضعیت این قراردادها لحاظ شده است (ستون "
        "«از این مبلغ، پرداخت امانی» را در جدول ببینید)."
    )

st.caption(
    f"⚙️ تنظیمات اعمال‌شده: قراردادهای منعقد از سال {_to_persian_digits(meta['since_jalali_year'])} "
    f"به بعد | آستانه رکود: {_to_persian_digits(meta['dormant_days_threshold'])} روز | "
    f"تاریخ مبنا: {_to_persian_digits(format_jalali(meta['as_of']))}"
)

if df.empty:
    st.info("هیچ قراردادی با معیارهای فعلی یافت نشد.")
    st.stop()

df["last_payment_date_jalali"] = df["last_payment_date"].apply(
    lambda d: "—" if pd.isna(d) else _to_persian_digits(format_jalali(d))
)

st.markdown("---")
st.subheader("🔎 فیلترها")
filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    status_filter = st.multiselect(
        "وضعیت:",
        options=STATUS_ORDER,
        default=STATUS_ORDER,
    )
with filter_col2:
    employer_filter = st.multiselect(
        "کارفرما (مشمول):",
        options=sorted(df["employer_name"].dropna().unique().tolist()),
    )
with filter_col3:
    university_filter = st.multiselect(
        "دانشگاه / موسسه مجری:",
        options=sorted(df["university_name"].dropna().unique().tolist()),
    )

# Employer/university narrow the whole analysis (KPIs, chart, and table);
# the status multiselect only narrows the detail table below, so the KPI
# cards keep showing the full status breakdown for the selected scope.
df_scope = df.copy()
if employer_filter:
    df_scope = df_scope[df_scope["employer_name"].isin(employer_filter)]
if university_filter:
    df_scope = df_scope[df_scope["university_name"].isin(university_filter)]

df_filtered = df_scope[df_scope["status"].isin(status_filter)] if status_filter else df_scope.iloc[0:0]

st.markdown("---")
st.subheader("🔑 شاخص‌های کلیدی")
kpi_cols = st.columns(4)
status_counts = df_scope["status"].value_counts()
for idx, status in enumerate(STATUS_ORDER):
    count = int(status_counts.get(status, 0))
    with kpi_cols[idx]:
        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #e5e7eb; border-right: 5px solid {STATUS_COLORS[status]};
                        border-radius: 8px; padding: 16px; text-align: center;
                        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                <div style="font-size: 14px; color: #6b7280;">{status}</div>
                <div style="font-size: 28px; font-weight: 700; color: #111827;">{_format_int(count)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

dormant_remaining = df_scope.loc[df_scope["status"] == "راکد", "remaining_amount"].sum()
st.markdown(
    f"""
    <div style="margin-top: 14px; background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px;
                padding: 14px; text-align: center;">
        <span style="color:#991B1B; font-weight:600;">💰 مجموع مانده باقی‌مانده قراردادهای راکد: </span>
        <span style="color:#991B1B; font-weight:700; font-size: 18px;">{_format_rials(dormant_remaining)} ریال</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")
st.subheader("📊 توزیع وضعیت قراردادها")
chart_counts = status_counts.reindex(STATUS_ORDER).fillna(0)
fig = go.Figure(
    go.Bar(
        x=[_to_persian_digits(int(v)) for v in chart_counts.values],
        y=chart_counts.index.tolist(),
        orientation="h",
        marker_color=[STATUS_COLORS[s] for s in chart_counts.index],
        text=[_to_persian_digits(int(v)) for v in chart_counts.values],
        textposition="auto",
    )
)
fig.update_layout(
    font=dict(family="Vazirmatn", size=14),
    xaxis=dict(title="تعداد قرارداد", tickfont=dict(family="Vazirmatn")),
    yaxis=dict(title="", autorange="reversed", tickfont=dict(family="Vazirmatn", size=13)),
    height=320,
    margin=dict(l=20, r=20, t=20, b=40),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="white",
    showlegend=False,
)
st.plotly_chart(fig, width="stretch", theme=None)

st.markdown("---")
st.subheader("📋 فهرست تفصیلی قراردادها")
st.caption(f"{_format_int(len(df_filtered))} قرارداد مطابق فیلترهای انتخاب‌شده")

status_priority = {s: i for i, s in enumerate(STATUS_ORDER)}
df_sorted = df_filtered.copy()
df_sorted["_status_priority"] = df_sorted["status"].map(status_priority)
df_sorted = df_sorted.sort_values(
    by=["_status_priority", "days_since_last_payment"],
    ascending=[True, False],
    na_position="first",
)

df_display = df_sorted[DETAIL_COLUMNS].rename(columns=DETAIL_LABELS)
for col_key in ("total_amount", "total_paid", "trustee_paid_amount", "remaining_amount"):
    df_display[DETAIL_LABELS[col_key]] = df_sorted[col_key].apply(_format_rials)
for col_key in ("contract_jalali_year", "days_since_last_payment"):
    df_display[DETAIL_LABELS[col_key]] = df_sorted[col_key].apply(_format_int)
df_display[DETAIL_LABELS["data_quality_flag"]] = df_sorted["data_quality_flag"].apply(
    _format_text
)

if df_display.empty:
    st.info("با فیلترهای فعلی هیچ قراردادی یافت نشد.")
else:
    st.table(df_display)

st.markdown("---")


def _to_excel(export_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Stagnant Contracts")
    output.seek(0)
    return output.getvalue()


export_df = df_sorted[DETAIL_COLUMNS].rename(columns=DETAIL_LABELS)
st.download_button(
    label="📥 دانلود فهرست کامل به صورت اکسل",
    data=_to_excel(export_df),
    file_name=f"contract_status_{meta['as_of'].isoformat()}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
