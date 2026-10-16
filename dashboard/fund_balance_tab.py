"""«ترازنامه دبیرخانه و صندوق» -- tab of the main dashboard.

Same idea as the «ترازنامه مشمولین» tab (pick an employer, see its position),
but every deposit / balance figure is shown twice: from OUR data and from the
Fund's report (kept up to date in parallel with our data entry; see
``services/fund_report.py``). All amounts are displayed in میلیون ریال.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from services.fund_report import MILLION, get_latest_snapshot, get_secretariat_fund_balance_sheet

# internal column -> Persian header (also the order of the exported table)
TABLE_COLUMNS = {
    "employer_code": "کد مشمول",
    "employer_name": "نام مشمول",
    "upper_organization": "سازمان بالادست",
    "our_deposit_1402": "واریزی ۱۴۰۲ - ما",
    "our_deposit_1404_1405": "واریزی ۱۴۰۴ به بعد - ما",
    "fund_deposit_1404": "واریزی ۱۴۰۴ به بعد - صندوق",
    "diff_deposit_1404": "اختلاف واریزی ۱۴۰۴ (صندوق - ما)",
    "our_expense_total": "هزینه‌کرد - ما",
    "fund_paid": "پرداختی - صندوق",
    "our_transfers_net": "خالص انتقال اعتبار - ما",
    "fund_credit_1402_1403": "اعتبار ۱۴۰۲-۱۴۰۳ - صندوق",
    "our_combined_balance": "مانده تجمیعی پس از انتقال اعتبار - ما",
    "our_unpaid_transfers": "انتقال اعتبار پرداخت‌نشده (تعهد) - ما",
    "our_balance_fund_basis": "مانده بر مبنای پرداخت - ما (قابل مقایسه با صندوق)",
    "fund_balance": "مانده - صندوق",
    "diff_balance": "اختلاف مانده (صندوق - مبنای پرداخت ما)",
    "fund_fee": "کارمزد صندوق (کسر نمی‌شود)",
    "fund_new_deposit": "واریزی بعد از گزارش صندوق (به‌روزشده)",
    "fund_new_paid": "پرداختی بعد از گزارش صندوق (به‌روزشده)",
    "fund_line_codes": "ردیف‌های صندوق (کد)",
}
MONEY_COLUMNS = [
    c for c in TABLE_COLUMNS
    if c not in ("employer_code", "employer_name", "upper_organization", "fund_line_codes")
]


def _to_million(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in MONEY_COLUMNS:
        out[column] = (out[column].astype(float) / MILLION).round(0)
    return out


def _excel_bytes(df_million: pd.DataFrame) -> bytes:
    export = df_million[list(TABLE_COLUMNS)].rename(columns=TABLE_COLUMNS)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export.to_excel(writer, index=False, sheet_name="ترازنامه دبیرخانه و صندوق")
        ws = writer.sheets["ترازنامه دبیرخانه و صندوق"]
        ws.sheet_view.rightToLeft = True
        ws.freeze_panes = "C2"
        for idx, column in enumerate(export.columns, start=1):
            ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = min(
                max(len(str(column)) + 2, 14), 40
            )
            if column in [TABLE_COLUMNS[c] for c in MONEY_COLUMNS]:
                for row in range(2, len(export) + 2):
                    ws.cell(row=row, column=idx).number_format = "#,##0"
    return buffer.getvalue()


def _fmt(value: float) -> str:
    return f"{value:,.0f}"


def render_fund_balance_tab(db) -> None:
    snapshot = get_latest_snapshot(db)
    if snapshot is None:
        st.warning(
            "هنوز گزارش صندوق در پایگاه داده ثبت نشده است. "
            "اجرا کنید: python scripts/import_fund_report.py <مسیر Sandogh_Report.xlsx>"
        )
        return

    with st.spinner("در حال محاسبهٔ ترازنامه دبیرخانه و صندوق..."):
        raw = get_secretariat_fund_balance_sheet(db, snapshot)
    if raw.empty:
        st.warning("داده‌ای برای نمایش وجود ندارد.")
        return
    df = _to_million(raw)

    st.subheader("⚖️ ترازنامه دبیرخانه و صندوق")
    st.caption(
        f"گزارش صندوق: «{snapshot.label}» — {snapshot.cutoff_note}. "
        f"واریزی‌ها و پرداخت‌هایی که پس از آن (سری پرداخت بعد از {snapshot.baseline_payment_series}) "
        "در سامانهٔ خودمان ثبت می‌شود، به‌صورت موازی به ستون‌های صندوق اضافه می‌شود. "
        "همهٔ مبالغ به میلیون ریال."
    )
    st.info(
        "صندوق فقط پرداخت‌ها را می‌بیند و سازوکار انتقال اعتبار ندارد: هر پرداخت را به مشمولی که "
        "اعتبارش را تأمین کرده و فقط هنگام پرداخت واقعی کسر می‌کند. در سامانهٔ ما کل مبلغ انتقالی "
        "برای مشمول مبدأ هزینه‌کرد حساب می‌شود و پرداخت از حساب کارگزار/مقصد کسر می‌شود. "
        "برای مقایسهٔ منصفانه، «مانده بر مبنای پرداخت - ما» = مانده ما پس از انتقال + انتقال "
        "پرداخت‌نشده (تعهد) است؛ اختلاف مانده نسبت به همین ستون محاسبه می‌شود."
    )
    st.info(
        f"به‌روزرسانی موازی تا الان: واریزی جدید {_fmt(raw['fund_new_deposit'].sum() / MILLION)} | "
        f"پرداختی جدید {_fmt(raw['fund_new_paid'].sum() / MILLION)} میلیون ریال"
    )

    st.markdown("---")
    st.markdown("### جمع کل مشمولین")
    # totals are summed from the unrounded figures, then converted
    total = raw.drop(columns=["employer_code", "employer_name", "upper_organization",
                              "fund_agency", "fund_line_codes", "in_fund_report"]).sum() / MILLION
    cols = st.columns(3)
    cols[0].metric("واریزی ۱۴۰۴ به بعد - ما", _fmt(total["our_deposit_1404_1405"]))
    cols[1].metric("واریزی ۱۴۰۴ به بعد - صندوق", _fmt(total["fund_deposit_1404"]),
                   delta=_fmt(total["diff_deposit_1404"]), delta_color="off")
    cols[2].metric("انتقال اعتبار پرداخت‌نشده (تعهد) - ما", _fmt(total["our_unpaid_transfers"]))
    cols = st.columns(3)
    cols[0].metric("مانده تجمیعی پس از انتقال - ما", _fmt(total["our_combined_balance"]))
    cols[1].metric("مانده بر مبنای پرداخت - ما", _fmt(total["our_balance_fund_basis"]))
    cols[2].metric("مانده - صندوق", _fmt(total["fund_balance"]),
                   delta=_fmt(total["diff_balance"]), delta_color="off")
    st.caption("عدد زیر «صندوق»، اختلاف صندوق منهای ما است (مانده: نسبت به مبنای پرداخت).")

    st.markdown("---")
    st.markdown("### ترازنامهٔ یک مشمول")
    options = {r.employer_code: f"{r.employer_code} - {r.employer_name}" for r in df.itertuples()}
    keys = list(options)
    default = keys.index("231500") if "231500" in keys else 0
    code = st.selectbox("انتخاب مشمول:", keys, index=default, format_func=options.get,
                        key="fund_tab_employer")
    row = df[df["employer_code"] == code].iloc[0]

    left, right = st.columns(2)
    with left:
        st.markdown("#### بر اساس داده‌های ما")
        st.metric("واریزی ۱۴۰۲", _fmt(row["our_deposit_1402"]))
        st.metric("واریزی ۱۴۰۴ به بعد", _fmt(row["our_deposit_1404_1405"]))
        st.metric("هزینه‌کرد (همهٔ سال‌ها)", _fmt(row["our_expense_total"]))
        st.metric("خالص انتقال اعتبار", _fmt(row["our_transfers_net"]))
        st.metric("💰 مانده تجمیعی (پس از انتقال)", _fmt(row["our_combined_balance"]))
        st.metric("انتقال اعتبار پرداخت‌نشده (تعهد)", _fmt(row["our_unpaid_transfers"]))
        st.metric("مانده بر مبنای پرداخت (قابل مقایسه با صندوق)", _fmt(row["our_balance_fund_basis"]))
    with right:
        st.markdown("#### بر اساس گزارش صندوق")
        st.metric("اعتبار ۱۴۰۲-۱۴۰۳", _fmt(row["fund_credit_1402_1403"]))
        st.metric("واریزی ۱۴۰۴ به بعد", _fmt(row["fund_deposit_1404"]))
        st.metric("پرداختی ۱۴۰۴ و ۱۴۰۵", _fmt(row["fund_paid"]))
        st.metric("کارمزد صندوق (کسر نمی‌شود)", _fmt(row["fund_fee"]))
        st.metric("💰 مانده", _fmt(row["fund_balance"]))

    diff_cols = st.columns(2)
    diff_cols[0].metric("اختلاف واریزی ۱۴۰۴ (صندوق - ما)", _fmt(row["diff_deposit_1404"]))
    diff_cols[1].metric("اختلاف مانده (صندوق - مبنای پرداخت ما)", _fmt(row["diff_balance"]))
    if not row["in_fund_report"]:
        st.warning("این مشمول در گزارش صندوق ردیفی ندارد (مقادیر صندوق صفر است).")
    elif row["fund_line_codes"] and "،" in row["fund_line_codes"]:
        st.caption(f"ردیف‌های صندوق تجمیع‌شده در این مشمول (کد): {row['fund_line_codes']}")

    st.markdown("---")
    st.markdown("### جدول مقایسهٔ همهٔ مشمولین")
    only_diff = st.checkbox("فقط ردیف‌های دارای اختلاف مانده (بیش از ۱ میلیون ریال)", key="fund_tab_only_diff")
    table = df[df["diff_balance"].abs() > 1] if only_diff else df
    st.dataframe(
        table[list(TABLE_COLUMNS)].rename(columns=TABLE_COLUMNS),
        hide_index=True,
        width="stretch",
        column_config={
            TABLE_COLUMNS[c]: st.column_config.NumberColumn(format="%d") for c in MONEY_COLUMNS
        },
    )
    st.download_button(
        "📥 دانلود ترازنامه دبیرخانه و صندوق (اکسل)",
        data=_excel_bytes(df),
        file_name="secretariat_fund_balance_sheet.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
