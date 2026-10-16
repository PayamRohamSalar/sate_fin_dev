"""داشبورد عملکرد گروه‌های سازمانی (هلدینگ‌ها و دستگاه‌های اجرایی).

Two independent grouping lenses over the same per-employer financial detail
(``services.financial_engine``):

1. **هلدینگ / شرکت مادرتخصصی** — ``Employer.holding_company_code``, a
   reporting-only grouping (added 2026-09-27) for employers that are fully
   financially independent but organizationally reported together (e.g. 31
   regional water companies under شرکت مادرتخصصی مدیریت منابع آب ایران).
   This is deliberately NOT the existing Mother/Subsidiary financial
   roll-up (``parent_code``) -- nothing here is merged or netted.
2. **دستگاه اجرایی / وزارتخانه** — ``Employer.upper_organization``, already
   populated on every employer; no new data needed.

Both use ``get_holding_group_financials`` / ``get_ministry_group_financials``
respectively, which return the same per-(employer, year) shape (plus an
optional "جمع گروه" total row), so this page renders them identically.

Reads directly from the database (no FastAPI backend needed), same pattern
as the project's other management dashboards.
"""

import io

import pandas as pd
import streamlit as st

from core.database import SessionLocal
from models.employer import Employer
from services.financial_engine import get_holding_group_financials, get_ministry_group_financials

MILLION = 1_000_000
SINCE_YEAR = 1402

DISPLAY_COLUMNS = {
    "employer_name": "مشمول",
    "year": "سال",
    "contracts_count": "تعداد قرارداد",
    "contracts_amount": "مبلغ قرارداد (میلیون ریال)",
    "mandated_amount": "اعتبار تکلیفی (میلیون ریال)",
    "deposit_amount": "واریزی (میلیون ریال)",
    "expense_amount": "هزینه‌کرد (میلیون ریال)",
}
MONEY_COLUMNS = ["contracts_amount", "mandated_amount", "deposit_amount", "expense_amount"]


@st.cache_resource
def _get_db():
    return SessionLocal()


def _to_display(df: pd.DataFrame) -> pd.DataFrame:
    """Scale money columns to million Rials and apply Persian headers."""
    out = df.copy()
    for col in MONEY_COLUMNS:
        out[col] = (out[col] / MILLION).round()
    return out[list(DISPLAY_COLUMNS)].rename(columns=DISPLAY_COLUMNS)


def _to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    output.seek(0)
    return output.getvalue()


def _render_group_table(df: pd.DataFrame, *, highlight_holding: bool, group_label: str) -> None:
    if df.empty:
        st.info(f"هیچ داده‌ای از سال {SINCE_YEAR} به بعد برای این گروه یافت نشد.")
        return

    years = sorted(df["year"].unique())
    tabs = st.tabs([f"سال {y}" for y in years] + ["همهٔ سال‌ها"])

    for tab, year in zip(tabs[:-1], years):
        with tab:
            year_df = _to_display(df[df["year"] == year])
            st.dataframe(year_df, use_container_width=True, hide_index=True)

    with tabs[-1]:
        st.dataframe(_to_display(df), use_container_width=True, hide_index=True)

    st.download_button(
        f"⬇️ دانلود اکسل ({group_label})",
        data=_to_excel_bytes({"جزئیات": _to_display(df)}),
        file_name=f"holding_group_{group_label}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


st.title("🏢 عملکرد گروه‌های سازمانی")
st.caption(f"تعداد و مبلغ قرارداد، اعتبار تکلیفی، واریزی و هزینه‌کرد -- از سال {SINCE_YEAR} تاکنون.")

db = _get_db()

tab_holding, tab_ministry = st.tabs(["🏗️ بر اساس هلدینگ / شرکت مادرتخصصی", "🏛️ بر اساس دستگاه اجرایی"])

with tab_holding:
    holdings = (
        db.query(Employer.classification_code, Employer.name)
        .filter(
            Employer.classification_code.in_(
                db.query(Employer.holding_company_code)
                .filter(Employer.holding_company_code.isnot(None), Employer.is_deleted == False)  # noqa: E712
                .distinct()
            ),
            Employer.is_deleted == False,  # noqa: E712
        )
        .order_by(Employer.name)
        .all()
    )
    if not holdings:
        st.info(
            "هنوز هیچ هلدینگی تعریف نشده. این گروه‌بندی از طریق "
            "`Employer.holding_company_code` (فقط برای گزارش‌گیری، بدون اثر "
            "بر محاسبات مالی موجود) تعریف می‌شود."
        )
    else:
        holding_options = {code: f"{name} ({code})" for code, name in holdings}
        selected_holding = st.selectbox(
            "شرکت مادرتخصصی / هلدینگ:",
            options=list(holding_options),
            format_func=holding_options.get,
        )
        df_holding = get_holding_group_financials(db, selected_holding, since_jalali_year=SINCE_YEAR)
        member_count = df_holding.loc[~df_holding["employer_name"].eq("جمع گروه"), "employer_code"].nunique()
        st.caption(f"{member_count} شرکت (شامل خود هلدینگ) در این گروه.")
        _render_group_table(df_holding, highlight_holding=True, group_label=holding_options[selected_holding])

with tab_ministry:
    ministries = [
        row[0]
        for row in db.query(Employer.upper_organization)
        .filter(Employer.is_deleted == False)  # noqa: E712
        .distinct()
        .order_by(Employer.upper_organization)
        .all()
        if row[0]
    ]
    selected_ministry = st.selectbox("دستگاه اجرایی / وزارتخانه:", options=ministries)
    df_ministry = get_ministry_group_financials(db, selected_ministry, since_jalali_year=SINCE_YEAR)
    member_count = df_ministry.loc[~df_ministry["employer_name"].eq("جمع گروه"), "employer_code"].nunique()
    st.caption(f"{member_count} مشمول (شرکت مادر و زیرمجموعه، هر کدام جداگانه) زیر این دستگاه.")
    _render_group_table(df_ministry, highlight_holding=False, group_label=selected_ministry)
