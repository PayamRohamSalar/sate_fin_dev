"""داشبورد تقاضا و پیشنهاده — عملکرد سمت تقاضا (کارفرمایان) و سمت عرضه
(پژوهشگران/دانشگاه‌ها) در ثبت فراخوان و ارسال پیشنهاده.

Reads directly from the database via ``services.demand_engine`` (read-only
analytics, does not need the FastAPI backend running), same DB-direct
pattern as the project's other management dashboards.
"""

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.database import SessionLocal
from core.date_helper import to_jalali_date
from services.demand_engine import STATUS_ORDER, get_proposal_details

TOP_N = 15
MIN_YEAR = 1398
DEFAULT_YEARS = [1402, 1403, 1404, 1405]
STATUS_COLORS = {
    "تایید نهایی": "#10B981",
    "رد": "#EF4444",
    "در انتظار تایید متقاضی": "#F59E0B",
    "در انتظار تایید موسسه / دانشگاه": "#F59E0B",
    "ذخیره موقت": "#9CA3AF",
    "در انتظار تایید مدیر سامانه": "#9CA3AF",
}
UNKNOWN_LABEL = "نامشخص"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, .stMultiSelect, .stSlider, .stRadio, p, div {
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


def _format_int(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{int(value):,}")


def _format_pct(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{value:,.1f}٪")


@st.cache_data(ttl=120, show_spinner=False)
def _load_proposal_details():
    db = SessionLocal()
    try:
        df = get_proposal_details(db)
    finally:
        db.close()
    df["employer_name"] = df["employer_name"].fillna(UNKNOWN_LABEL)
    df["status_title"] = df["status_title"].fillna(UNKNOWN_LABEL)
    df["submission_year"] = df["submitted_at"].apply(
        lambda dt: to_jalali_date(dt.date()).year if pd.notna(dt) else None
    )
    # Scope the whole dashboard to 1398 onward -- earlier rows are a
    # handful of pre-system-launch stragglers (including one clearly
    # mistaken 1366 date) that just distort the year-trend chart.
    df = df[df["submission_year"] >= MIN_YEAR].copy()
    return df


st.markdown(
    "<h1 style='text-align: center;'>📮 داشبورد تقاضا و پیشنهاده</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h4 style='text-align: center; color: gray;'>عملکرد کارفرمایان در جذب پیشنهاده و پژوهشگران/دانشگاه‌ها در ارسال آن</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

with st.expander("ℹ️ توضیح دامنه بررسی", expanded=True):
    st.markdown(
        "این داشبورد بر پایهٔ جدول‌های `demands` (فراخوان‌های ثبت‌شده توسط "
        "کارفرمایان) و `proposals` (پیشنهاده‌های ارسالی پژوهشگران/دانشگاه‌ها "
        "در پاسخ به آن‌ها) ساخته شده است."
    )
    st.caption(
        "نام کارفرما از طریق تقاضای مرتبط با هر پیشنهاده به دست می‌آید — "
        "برای پیشنهاده‌هایی که تقاضای آن‌ها یا کارفرمای آن تقاضا در پایگاه "
        "داده با نام دقیق یافت نشود، برچسب «نامشخص» نمایش داده می‌شود "
        "(حدود ۱۰٪ از کل پیشنهاده‌ها)."
    )
    st.caption(
        f"این داشبورد فقط پیشنهاده‌های ارسالی از سال {_to_persian_digits(MIN_YEAR)} به بعد را در نظر "
        "می‌گیرد؛ سال(های) موردنظر را با فیلتر زیر محدودتر هم می‌توانید انتخاب کنید."
    )

with st.spinner("در حال بارگذاری داده‌های تقاضا و پیشنهاده..."):
    df_all = _load_proposal_details()

if df_all.empty:
    st.info(f"هیچ پیشنهاده‌ای از سال {_to_persian_digits(MIN_YEAR)} به بعد در پایگاه داده یافت نشد.")
    st.stop()

st.markdown("---")
st.subheader("🗓️ فیلتر سال")
available_years = sorted(df_all["submission_year"].dropna().astype(int).unique().tolist())
default_years = [y for y in DEFAULT_YEARS if y in available_years] or available_years
selected_years = st.multiselect(
    "سال ارسال پیشنهاده (یک یا چند سال):",
    options=available_years,
    default=default_years,
    format_func=lambda y: _to_persian_digits(y),
)

if not selected_years:
    st.warning("حداقل یک سال را انتخاب کنید.")
    st.stop()

df = df_all[df_all["submission_year"].isin(selected_years)]

if df.empty:
    st.info("برای سال(های) انتخاب‌شده داده‌ای یافت نشد.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔑 شاخص‌های کلیدی")
kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.metric("تعداد پیشنهاده", _format_int(len(df)))
with kpi_cols[1]:
    st.metric("تعداد تقاضای دارای پیشنهاده", _format_int(df["demand_tracking_code"].nunique()))
with kpi_cols[2]:
    st.metric("تعداد پژوهشگر/فناور فرستنده", _format_int(df["researcher_code"].nunique()))
with kpi_cols[3]:
    approved_pct = (df["status_title"] == "تایید نهایی").mean() * 100
    st.metric("درصد تأییدشده", _format_pct(approved_pct))
with kpi_cols[4]:
    rejected_pct = (df["status_title"] == "رد").mean() * 100
    st.metric("درصد ردشده", _format_pct(rejected_pct))

# ── 1) وضعیت پیشنهاده‌ها ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 وضعیت پیشنهاده‌ها")
status_counts = df["status_title"].value_counts()
status_order = [s for s in STATUS_ORDER if s in status_counts.index] + [
    s for s in status_counts.index if s not in STATUS_ORDER
]
status_counts = status_counts.reindex(status_order)

fig_status = go.Figure(
    go.Bar(
        x=status_counts.values,
        y=status_counts.index,
        orientation="h",
        marker_color=[STATUS_COLORS.get(s, "#6B7280") for s in status_counts.index],
        text=[
            _to_persian_digits(f"{v:,} ({v / len(df) * 100:.1f}٪)")
            for v in status_counts.values
        ],
        textposition="auto",
    )
)
fig_status.update_layout(
    font=dict(family="Vazirmatn", size=14),
    xaxis=dict(title="تعداد پیشنهاده", tickfont=dict(family="Vazirmatn")),
    yaxis=dict(title="", autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
    height=340,
    margin=dict(l=10, r=10, t=10, b=40),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="white",
    showlegend=False,
)
st.plotly_chart(fig_status, width="stretch", theme=None)

# ── 2) روند ارسال به تفکیک سال ───────────────────────────────────────────────
st.markdown("---")
st.subheader("📈 روند ارسال پیشنهاده به تفکیک سال")
by_year = df.dropna(subset=["submission_year"]).groupby("submission_year").size()
by_year.index = by_year.index.astype(int)
by_year = by_year.sort_index()

fig_year = go.Figure(
    go.Bar(
        x=[_to_persian_digits(y) for y in by_year.index],
        y=by_year.values,
        marker_color="#3B82F6",
        text=[_to_persian_digits(f"{v:,}") for v in by_year.values],
        textposition="auto",
    )
)
fig_year.update_layout(
    font=dict(family="Vazirmatn", size=14),
    xaxis=dict(title="سال (شمسی)", tickfont=dict(family="Vazirmatn")),
    yaxis=dict(title="تعداد پیشنهاده ارسالی", tickfont=dict(family="Vazirmatn")),
    height=380,
    margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="white",
    showlegend=False,
)
st.plotly_chart(fig_year, width="stretch", theme=None)

# ── 3) رتبه‌بندی کارفرمایان بر اساس جذب پیشنهاده ─────────────────────────────
st.markdown("---")
st.subheader("🏢 رتبه‌بندی کارفرمایان بر اساس تعداد پیشنهادهٔ دریافتی")
st.caption("بر اساس کارفرمای صاحب تقاضایی که هر پیشنهاده به آن پاسخ داده است.")

by_employer = (
    df[df["employer_name"] != UNKNOWN_LABEL]
    .groupby("employer_name")
    .size()
    .sort_values(ascending=False)
)

direction = st.radio(
    "نمایش:", options=["بیشترین جذب", "کمترین جذب"], horizontal=True, key="employer_direction"
)
chart_employer = (
    by_employer.head(TOP_N) if direction == "بیشترین جذب" else by_employer.tail(TOP_N).sort_values()
)

fig_employer = go.Figure(
    go.Bar(
        x=chart_employer.values,
        y=chart_employer.index,
        orientation="h",
        marker_color="#8B5CF6",
        text=[_to_persian_digits(f"{v:,}") for v in chart_employer.values],
        textposition="auto",
    )
)
fig_employer.update_layout(
    font=dict(family="Vazirmatn", size=13),
    xaxis=dict(title="تعداد پیشنهادهٔ دریافتی", tickfont=dict(family="Vazirmatn")),
    yaxis=dict(title="", autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
    height=max(320, 30 * len(chart_employer)),
    margin=dict(l=10, r=10, t=10, b=40),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="white",
    showlegend=False,
)
st.caption(f"{_to_persian_digits(TOP_N)} کارفرمای دارای {direction.replace('جذب', 'میزان جذب')} پیشنهاده")
st.plotly_chart(fig_employer, width="stretch", theme=None)

# ── 4) رتبه‌بندی پژوهشگران بر اساس ارسال پیشنهاده ────────────────────────────
st.markdown("---")
st.subheader("🧑‍🔬 رتبه‌بندی پژوهشگران/فناوران بر اساس تعداد پیشنهادهٔ ارسالی")

by_researcher = (
    df.groupby(["researcher_name", "university_name"], dropna=False)
    .size()
    .reset_index(name="proposal_count")
    .sort_values("proposal_count", ascending=False)
    .head(TOP_N)
)
by_researcher["university_name"] = by_researcher["university_name"].fillna(UNKNOWN_LABEL)
labels = [
    f"{name} ({uni})" for name, uni in zip(by_researcher["researcher_name"], by_researcher["university_name"])
]

fig_researcher = go.Figure(
    go.Bar(
        x=by_researcher["proposal_count"],
        y=labels,
        orientation="h",
        marker_color="#F97316",
        text=[_to_persian_digits(f"{v:,}") for v in by_researcher["proposal_count"]],
        textposition="auto",
    )
)
fig_researcher.update_layout(
    font=dict(family="Vazirmatn", size=13),
    xaxis=dict(title="تعداد پیشنهادهٔ ارسالی", tickfont=dict(family="Vazirmatn")),
    yaxis=dict(title="", autorange="reversed", tickfont=dict(family="Vazirmatn", size=11)),
    height=max(320, 30 * len(by_researcher)),
    margin=dict(l=10, r=10, t=10, b=40),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="white",
    showlegend=False,
)
st.caption(f"{_to_persian_digits(TOP_N)} پژوهشگر/فناور دارای بیشترین تعداد پیشنهادهٔ ارسالی")
st.plotly_chart(fig_researcher, width="stretch", theme=None)

# ── 5) تبدیل پیشنهادهٔ تأییدشده به قرارداد ───────────────────────────────────
st.markdown("---")
st.subheader("📄 پیشنهادهای تأییدشده: با قرارداد در برابر بدون قرارداد")

approved = df[df["status_title"] == "تایید نهایی"]
with_contract = int(approved["has_contract"].sum())
without_contract = len(approved) - with_contract

conv_col1, conv_col2 = st.columns([1, 2])
with conv_col1:
    st.metric("تعداد تأییدشده", _format_int(len(approved)))
    st.metric("دارای قرارداد", _format_int(with_contract))
    st.metric("بدون قرارداد", _format_int(without_contract))
    if len(approved) > 0:
        st.metric("نرخ تبدیل به قرارداد", _format_pct(with_contract / len(approved) * 100))

with conv_col2:
    fig_conv = go.Figure(
        go.Pie(
            labels=["دارای قرارداد", "بدون قرارداد"],
            values=[with_contract, without_contract],
            marker=dict(colors=["#10B981", "#EF4444"]),
            textinfo="label+percent",
            textfont=dict(family="Vazirmatn", size=14),
        )
    )
    fig_conv.update_layout(
        font=dict(family="Vazirmatn", size=13),
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        showlegend=False,
    )
    st.plotly_chart(fig_conv, width="stretch", theme=None)

# ── جدول تفصیلی + خروجی اکسل ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 فهرست تفصیلی پیشنهاده‌ها")

st.caption("این جدول هم مطابق فیلتر سال بالای صفحه محدود شده؛ فیلترهای زیر روی همان بازه اعمال می‌شوند.")
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    employer_filter = st.multiselect(
        "کارفرما:", options=sorted(df["employer_name"].unique().tolist())
    )
with filter_col2:
    status_filter = st.multiselect(
        "وضعیت:", options=sorted(df["status_title"].unique().tolist())
    )

df_filtered = df.copy()
if employer_filter:
    df_filtered = df_filtered[df_filtered["employer_name"].isin(employer_filter)]
if status_filter:
    df_filtered = df_filtered[df_filtered["status_title"].isin(status_filter)]

st.caption(f"{_format_int(len(df_filtered))} پیشنهاده مطابق فیلترهای انتخاب‌شده")

DETAIL_COLUMNS = [
    "proposal_id", "employer_name", "demand_title", "researcher_name",
    "university_name", "status_title", "submitted_at", "has_contract",
    "contract_tracking_code",
]
DETAIL_LABELS = {
    "proposal_id": "شناسه پیشنهاده",
    "employer_name": "کارفرما",
    "demand_title": "عنوان تقاضا",
    "researcher_name": "پژوهشگر/فناور",
    "university_name": "دانشگاه/موسسه",
    "status_title": "وضعیت",
    "submitted_at": "تاریخ ارسال",
    "has_contract": "منجر به قرارداد",
    "contract_tracking_code": "کد رهگیری قرارداد",
}

df_display = df_filtered[DETAIL_COLUMNS].rename(columns=DETAIL_LABELS).copy()
df_display[DETAIL_LABELS["has_contract"]] = df_filtered["has_contract"].map({True: "بله", False: "خیر"})
df_display[DETAIL_LABELS["contract_tracking_code"]] = df_filtered["contract_tracking_code"].fillna("—")

if df_display.empty:
    st.info("با فیلترهای فعلی داده‌ای یافت نشد.")
else:
    st.table(df_display.head(500))
    if len(df_display) > 500:
        st.caption("فقط ۵۰۰ ردیف اول نمایش داده می‌شود؛ برای فهرست کامل از دکمهٔ دانلود استفاده کنید.")


def _to_excel(export_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Proposals")
    output.seek(0)
    return output.getvalue()


export_df = df_filtered[DETAIL_COLUMNS].rename(columns=DETAIL_LABELS)
st.download_button(
    label="📥 دانلود فهرست کامل به صورت اکسل",
    data=_to_excel(export_df),
    file_name="proposals_detail.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
