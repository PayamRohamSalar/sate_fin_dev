"""داشبورد رتبه‌بندی دانشگاه‌ها و جریان مالی هلدینگ‌ها به دانشگاه‌ها (Sankey).

Reads directly from the database via ``services.financial_engine``, the same
DB-direct pattern used by ``dashboard/app.py``'s management dashboards and
the other analytics pages under "داشبوردهای مدیریتی" (read-only analytics,
not a data-entry form — does not need the FastAPI backend running).
"""

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.database import SessionLocal
from services.financial_engine import get_employer_university_fund_flow

DEFAULT_SINCE_JALALI_YEAR = 1402
DEFAULT_TOP_N_EMPLOYERS = 8
DEFAULT_TOP_N_UNIVERSITIES = 8

METRIC_OPTIONS = {
    "مبلغ پرداخت‌شده (واقعی)": "payments_amount",
    "مبلغ قرارداد (تعهدشده)": "contracts_amount",
}

OTHER_EMPLOYER_LABEL = "سایر کارفرمایان"
OTHER_UNIVERSITY_LABEL = "سایر دانشگاه‌ها"

RANKING_COLUMNS = [
    "university_name",
    "province",
    "university_type",
    "distinct_employers_count",
    "contracts_count",
    "contracts_amount",
    "payments_amount",
]
RANKING_LABELS = {
    "university_name": "نام دانشگاه / موسسه",
    "province": "استان",
    "university_type": "نوع موسسه",
    "distinct_employers_count": "تعداد کارفرمایان همکار",
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
def _load_fund_flow(since_jalali_year):
    """Cached load of the (employer, university) fund-flow pair table."""
    db = SessionLocal()
    try:
        df, meta = get_employer_university_fund_flow(db, since_jalali_year=since_jalali_year)
    finally:
        db.close()
    return df, meta


def _regroup_top_n(df: pd.DataFrame, metric_col: str, top_n_employers: int, top_n_universities: int) -> pd.DataFrame:
    """Collapse employers/universities outside the top-N (by metric total) into "سایر" buckets."""
    employer_totals = df.groupby("employer_name")[metric_col].sum().sort_values(ascending=False)
    university_totals = df.groupby("university_name")[metric_col].sum().sort_values(ascending=False)

    top_employers = set(employer_totals.head(top_n_employers).index)
    top_universities = set(university_totals.head(top_n_universities).index)

    regrouped = df.copy()
    regrouped["employer_display"] = regrouped["employer_name"].where(
        regrouped["employer_name"].isin(top_employers), OTHER_EMPLOYER_LABEL
    )
    regrouped["university_display"] = regrouped["university_name"].where(
        regrouped["university_name"].isin(top_universities), OTHER_UNIVERSITY_LABEL
    )
    return (
        regrouped.groupby(["employer_display", "university_display"], as_index=False)[metric_col]
        .sum()
    )


def _render_sankey(links: pd.DataFrame, metric_col: str, metric_label: str):
    links = links[links[metric_col] > 0]
    if links.empty:
        st.info("داده‌ای برای رسم نمودار جریان یافت نشد.")
        return

    employer_nodes = links["employer_display"].unique().tolist()
    # Keep "سایر کارفرمایان" last among employer nodes for a cleaner layout.
    employer_nodes = sorted(employer_nodes, key=lambda n: n == OTHER_EMPLOYER_LABEL)
    university_nodes = links["university_display"].unique().tolist()
    university_nodes = sorted(university_nodes, key=lambda n: n == OTHER_UNIVERSITY_LABEL)

    all_nodes = employer_nodes + university_nodes
    node_index = {name: i for i, name in enumerate(all_nodes)}

    employer_color = "#3B82F6"
    other_employer_color = "#93C5FD"
    university_color = "#10B981"
    other_university_color = "#6EE7B7"
    node_colors = (
        [other_employer_color if n == OTHER_EMPLOYER_LABEL else employer_color for n in employer_nodes]
        + [other_university_color if n == OTHER_UNIVERSITY_LABEL else university_color for n in university_nodes]
    )

    source = [node_index[e] for e in links["employer_display"]]
    target = [node_index[u] for u in links["university_display"]]
    value = links[metric_col].tolist()

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=18,
                thickness=18,
                label=all_nodes,
                color=node_colors,
                line=dict(color="#374151", width=0.5),
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color="rgba(59, 130, 246, 0.25)",
                label=[f"{_to_persian_digits(f'{v:,.0f}')} ریال" for v in value],
            ),
        )
    )
    fig.update_layout(
        font=dict(family="Vazirmatn", size=13),
        title=dict(
            text=f"جریان {metric_label} از کارفرمایان به دانشگاه‌ها",
            x=0.5, xanchor="center", font=dict(family="Vazirmatn", size=16),
        ),
        height=max(420, 32 * len(all_nodes)),
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, width="stretch", theme=None)


st.markdown(
    "<h1 style='text-align: center;'>🎓 داشبورد رتبه‌بندی دانشگاه‌ها</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h4 style='text-align: center; color: gray;'>جریان مالی کارفرمایان به دانشگاه‌ها و رتبه‌بندی جذب بودجه پژوهشی</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

with st.expander("ℹ️ توضیح دامنه بررسی", expanded=True):
    st.markdown(
        "این داشبورد قراردادهای **منعقد شده از سال ۱۴۰۲ به بعد** (بر اساس "
        "تاریخ قرارداد) را بررسی می‌کند. دو معیار قابل انتخاب است:"
    )
    st.markdown(
        "- **مبلغ پرداخت‌شده (واقعی):** پولی که واقعاً به دانشگاه/موسسه پرداخت شده — "
        "معیار پیش‌فرض برای «جذب موفق بودجه».\n"
        "- **مبلغ قرارداد (تعهدشده):** ارزش کل قراردادهای منعقد شده، صرف‌نظر از میزان پرداخت.\n"
    )
    st.caption(
        "چون فقط شرکت‌های «مادر» و «مستقل» مجاز به انعقاد قرارداد هستند، هر "
        "کارفرما در این داشبورد به‌صورت مستقیم (بدون نیاز به تجمیع زیرمجموعه) "
        "نمایش داده می‌شود."
    )

with st.expander("⚙️ تنظیمات پیشرفته (تعداد گره‌های نمودار جریان)"):
    col_a, col_b = st.columns(2)
    with col_a:
        top_n_employers = st.slider(
            "تعداد کارفرمایان نمایش داده‌شده در نمودار (باقی = «سایر»):",
            min_value=3, max_value=15, value=DEFAULT_TOP_N_EMPLOYERS, step=1,
        )
    with col_b:
        top_n_universities = st.slider(
            "تعداد دانشگاه‌ها نمایش داده‌شده در نمودار (باقی = «سایر»):",
            min_value=3, max_value=15, value=DEFAULT_TOP_N_UNIVERSITIES, step=1,
        )

with st.spinner("در حال بارگذاری داده‌های قرارداد و پرداخت..."):
    df_pairs, meta = _load_fund_flow(int(DEFAULT_SINCE_JALALI_YEAR))

if meta["excluded_no_contract_date"] > 0:
    st.warning(
        f"⚠️ {_format_int(meta['excluded_no_contract_date'])} قرارداد فاقد "
        "تاریخ ثبت‌شده هستند و از این تحلیل کنار گذاشته شدند."
    )

if df_pairs.empty:
    st.info(f"هیچ قراردادی از سال {_to_persian_digits(DEFAULT_SINCE_JALALI_YEAR)} به بعد یافت نشد.")
    st.stop()

st.markdown("---")
metric_label = st.radio("معیار نمایش:", options=list(METRIC_OPTIONS.keys()), horizontal=True)
metric_col = METRIC_OPTIONS[metric_label]

st.markdown("---")
st.subheader("🔑 شاخص‌های کلیدی")
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("تعداد دانشگاه‌ها/موسسات دارای قرارداد", _format_int(df_pairs["university_name"].nunique()))
with kpi_cols[1]:
    st.metric("تعداد کارفرمایان دارای قرارداد", _format_int(df_pairs["employer_name"].nunique()))
with kpi_cols[2]:
    st.metric("مجموع مبلغ قراردادها (ریال)", _format_rials(df_pairs["contracts_amount"].sum()))
with kpi_cols[3]:
    st.metric("مجموع مبلغ پرداختی (ریال)", _format_rials(df_pairs["payments_amount"].sum()))

st.markdown("---")
st.subheader("🌊 نمودار جریان مالی کارفرما ← دانشگاه")
st.caption(
    "برای خوانایی، فقط کارفرمایان و دانشگاه‌های برتر (طبق تنظیمات پیشرفته بالا) "
    "به‌صورت جداگانه نمایش داده می‌شوند؛ بقیه در گره «سایر» تجمیع شده‌اند."
)
links = _regroup_top_n(df_pairs, metric_col, top_n_employers, top_n_universities)
_render_sankey(links, metric_col, metric_label)

st.markdown("---")
st.subheader("📊 رتبه‌بندی دانشگاه‌ها بر اساس " + metric_label)
ranking = (
    df_pairs.groupby(["university_name", "province", "university_type"], as_index=False)
    .agg(
        distinct_employers_count=("employer_name", "nunique"),
        contracts_count=("contracts_count", "sum"),
        contracts_amount=("contracts_amount", "sum"),
        payments_amount=("payments_amount", "sum"),
    )
    .sort_values(metric_col, ascending=False)
)

chart_ranking = ranking.head(15)
fig_rank = go.Figure(
    go.Bar(
        x=chart_ranking[metric_col],
        y=chart_ranking["university_name"],
        orientation="h",
        marker_color="#10B981",
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
st.caption("۱۵ دانشگاه/موسسه برتر بر اساس معیار انتخاب‌شده")
st.plotly_chart(fig_rank, width="stretch", theme=None)

st.markdown("---")
st.subheader("📋 فهرست کامل رتبه‌بندی")

province_filter = st.multiselect("استان:", options=sorted(ranking["province"].dropna().unique().tolist()))
ranking_filtered = ranking[ranking["province"].isin(province_filter)] if province_filter else ranking
st.caption(f"{_format_int(len(ranking_filtered))} دانشگاه/موسسه مطابق فیلتر")

ranking_display = ranking_filtered[RANKING_COLUMNS].rename(columns=RANKING_LABELS)
for col_key in ("distinct_employers_count", "contracts_count"):
    ranking_display[RANKING_LABELS[col_key]] = ranking_filtered[col_key].apply(_format_int)
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
        export_df.to_excel(writer, index=False, sheet_name="University Ranking")
    output.seek(0)
    return output.getvalue()


export_df = ranking_filtered[RANKING_COLUMNS].rename(columns=RANKING_LABELS)
st.download_button(
    label="📥 دانلود رتبه‌بندی به صورت اکسل",
    data=_to_excel(export_df),
    file_name="university_ranking.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
