"""داشبورد رتبه‌بندی پژوهشگران/فناوران (سمت عرضه) بر اساس تعداد و مبلغ قرارداد،
و حجم مبالغ دریافتی.

Reads directly from the database via ``services.financial_engine``, same
DB-direct pattern as ``university_ranking_dashboard.py`` (read-only
analytics, does not need the FastAPI backend running).
"""

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.database import SessionLocal
from services.financial_engine import get_researcher_contract_activity

DEFAULT_SINCE_JALALI_YEAR = 1402
DEFAULT_TOP_N = 15

METRIC_OPTIONS = {
    "مبلغ پرداخت‌شده (واقعی)": "payments_amount",
    "مبلغ قرارداد (تعهدشده)": "contracts_amount",
}

RANKING_COLUMNS = [
    "researcher_name",
    "academic_rank",
    "university_name",
    "province",
    "contracts_count",
    "contracts_amount",
    "payments_amount",
]
RANKING_LABELS = {
    "researcher_name": "نام پژوهشگر/فناور",
    "academic_rank": "رتبه علمی",
    "university_name": "دانشگاه/موسسه",
    "province": "استان",
    "contracts_count": "تعداد قرارداد",
    "contracts_amount": "مجموع مبلغ قرارداد (ریال)",
    "payments_amount": "مجموع دریافتی (ریال)",
}

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


def _format_rials(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{value:,.0f}")


def _format_int(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return _to_persian_digits(f"{int(value):,}")


@st.cache_data(ttl=120, show_spinner=False)
def _load_researcher_activity(since_jalali_year):
    db = SessionLocal()
    try:
        df, meta = get_researcher_contract_activity(db, since_jalali_year=since_jalali_year)
    finally:
        db.close()
    return df, meta


st.markdown(
    "<h1 style='text-align: center;'>🧑‍🔬 داشبورد رتبه‌بندی پژوهشگران/فناوران</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h4 style='text-align: center; color: gray;'>عملکرد سمت عرضه به تفکیک پژوهشگر مجری طرح</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

with st.expander("ℹ️ توضیح دامنه بررسی", expanded=True):
    st.markdown(
        "این داشبورد قراردادهای **منعقد شده از سال ۱۴۰۲ به بعد** (بر اساس "
        "تاریخ قرارداد) را بر اساس پژوهشگر مجری طرح (نه دانشگاه) گروه‌بندی "
        "می‌کند. دو معیار قابل انتخاب است:"
    )
    st.markdown(
        "- **مبلغ پرداخت‌شده (واقعی):** پولی که واقعاً به قرارداد این پژوهشگر پرداخت شده.\n"
        "- **مبلغ قرارداد (تعهدشده):** ارزش کل قراردادهای این پژوهشگر، صرف‌نظر از میزان پرداخت.\n"
    )
    st.caption(
        "هر قرارداد دقیقاً یک پژوهشگر مجری دارد (``Contract.researcher_id``)؛ "
        "دانشگاه/استان نمایش داده‌شده از پروندهٔ خود پژوهشگر خوانده می‌شود، نه از قرارداد."
    )

with st.spinner("در حال بارگذاری داده‌های قرارداد و پرداخت..."):
    df, meta = _load_researcher_activity(int(DEFAULT_SINCE_JALALI_YEAR))

if meta["excluded_no_contract_date"] > 0:
    st.warning(
        f"⚠️ {_format_int(meta['excluded_no_contract_date'])} قرارداد فاقد "
        "تاریخ ثبت‌شده هستند و از این تحلیل کنار گذاشته شدند."
    )

if df.empty:
    st.info(f"هیچ قراردادی از سال {_to_persian_digits(DEFAULT_SINCE_JALALI_YEAR)} به بعد یافت نشد.")
    st.stop()

st.markdown("---")
metric_label = st.radio("معیار نمایش:", options=list(METRIC_OPTIONS.keys()), horizontal=True)
metric_col = METRIC_OPTIONS[metric_label]

st.markdown("---")
st.subheader("🔑 شاخص‌های کلیدی")
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("تعداد پژوهشگران دارای قرارداد", _format_int(df["researcher_national_code"].nunique()))
with kpi_cols[1]:
    st.metric("تعداد دانشگاه/موسسهٔ نماینده‌شده", _format_int(df["university_name"].nunique()))
with kpi_cols[2]:
    st.metric("مجموع مبلغ قراردادها (ریال)", _format_rials(df["contracts_amount"].sum()))
with kpi_cols[3]:
    st.metric("مجموع مبلغ پرداختی (ریال)", _format_rials(df["payments_amount"].sum()))

st.markdown("---")
st.subheader("📊 رتبه‌بندی پژوهشگران بر اساس " + metric_label)
ranking = df.sort_values(metric_col, ascending=False)
chart_ranking = ranking.head(DEFAULT_TOP_N)

fig_rank = go.Figure(
    go.Bar(
        x=chart_ranking[metric_col],
        y=chart_ranking["researcher_name"],
        orientation="h",
        marker_color="#8B5CF6",
        text=[_to_persian_digits(f"{v:,.0f}") for v in chart_ranking[metric_col]],
        textposition="auto",
    )
)
fig_rank.update_layout(
    font=dict(family="Vazirmatn", size=14),
    xaxis=dict(title=metric_label + " (ریال)", tickfont=dict(family="Vazirmatn")),
    yaxis=dict(title="", autorange="reversed", tickfont=dict(family="Vazirmatn", size=12)),
    height=max(320, 28 * len(chart_ranking)),
    margin=dict(l=20, r=20, t=20, b=40),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="white",
    showlegend=False,
)
st.caption(f"{_to_persian_digits(DEFAULT_TOP_N)} پژوهشگر برتر بر اساس معیار انتخاب‌شده")
st.plotly_chart(fig_rank, width="stretch", theme=None)

st.markdown("---")
st.subheader("📋 فهرست کامل رتبه‌بندی")

filter_cols = st.columns(2)
with filter_cols[0]:
    university_filter = st.multiselect(
        "دانشگاه/موسسه:", options=sorted(ranking["university_name"].dropna().unique().tolist())
    )
with filter_cols[1]:
    rank_filter = st.multiselect(
        "رتبه علمی:", options=sorted(ranking["academic_rank"].dropna().unique().tolist())
    )

ranking_filtered = ranking
if university_filter:
    ranking_filtered = ranking_filtered[ranking_filtered["university_name"].isin(university_filter)]
if rank_filter:
    ranking_filtered = ranking_filtered[ranking_filtered["academic_rank"].isin(rank_filter)]

st.caption(f"{_format_int(len(ranking_filtered))} پژوهشگر مطابق فیلتر")

ranking_display = ranking_filtered[RANKING_COLUMNS].rename(columns=RANKING_LABELS)
ranking_display[RANKING_LABELS["contracts_count"]] = ranking_filtered["contracts_count"].apply(_format_int)
for col_key in ("contracts_amount", "payments_amount"):
    ranking_display[RANKING_LABELS[col_key]] = ranking_filtered[col_key].apply(_format_rials)

if ranking_display.empty:
    st.info("با فیلتر فعلی داده‌ای یافت نشد.")
else:
    st.table(ranking_display)

st.markdown("---")


def _to_excel(export_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Researcher Ranking")
    output.seek(0)
    return output.getvalue()


export_df = ranking_filtered[RANKING_COLUMNS].rename(columns=RANKING_LABELS)
st.download_button(
    label="📥 دانلود رتبه‌بندی به صورت اکسل",
    data=_to_excel(export_df),
    file_name="researcher_ranking.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
