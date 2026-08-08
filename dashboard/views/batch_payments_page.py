"""Render the database-backed batch payment (draft/finalize) form.

Every draft is persisted to the ``payments`` table the moment it is added
(``POST /payments/draft``), so the list survives a browser reload. Funds
are reserved against the employer's real balance as soon as a draft is
created — the backend hard-blocks (HTTP 400) any payment that would take
the balance negative, superseding the old FR-18/19/20 warning-only rule.
"""

import io

import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/v1"

# Exact Persian headers/order required for both the on-screen drafts table
# and the finalized-batch Excel export.
DRAFT_TABLE_COLUMNS = [
    "کد رهگیری پرداخت",
    "کد قرارداد",
    "متقاضی",
    "دانشگاه یا موسسه مجری",
    "عنوان قرارداد",
    "مبلغ قرارداد (ریال)",
    "مبلغ پرداختی (ریال)",
    "پرداخت از محل سال مالی",
    "مانده متقاضی (ریال)",
]
NUMERIC_TABLE_COLUMNS = [
    "مبلغ قرارداد (ریال)",
    "مبلغ پرداختی (ریال)",
    "مانده متقاضی (ریال)",
]

# Widgets cleared after a successful "Add to Batch" — everything about the
# row just added, but not the global series/payment-year config.
ROW_RESET_KEYS = (
    "batch_search_query",
    "batch_contract_choice",
    "batch_pay_tracking_code",
    "batch_amount",
    "batch_funding_year",
)

FINALIZE_STATE_KEY = "batch_finalize_state"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
    h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
    hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
    .stBlock, .stVerticalBlock, [data-testid="stVerticalBlock"] > div {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    /* st.table renders a real HTML <table> (unlike st.dataframe, which draws
       cells on a <canvas> that ignores page CSS entirely — the root cause
       of the font/RTL/number-ordering bugs in the drafts table). */
    table, th, td, .stTable, [data-testid="stTable"] * {
        font-family: 'Vazirmatn', sans-serif !important;
        font-size: 15px !important;
        text-align: center !important;
        direction: rtl !important;
    }
    th { background-color: #f0f2f6 !important; border-bottom: 2px solid #4a4a4a !important; color: black !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📂 فرم ثبت دسته‌ای لیست پرداخت (کارتابل صندوق عتف)")


PERSIAN_DIGITS = {
    "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
    "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
}


def _to_persian_digits(text) -> str:
    """Convert ASCII digits to Persian digits.

    Western digits inside an RTL-directed comma-separated number are prone
    to bidi reordering in the browser (the exact "balance is messed up"
    symptom) — Persian digits are treated as part of the surrounding RTL
    run and render in the correct order, matching the convention already
    used for on-screen numbers elsewhere in this app (``dashboard/app.py``'s
    ``to_persian_numbers``).
    """
    text = str(text)
    for eng, per in PERSIAN_DIGITS.items():
        text = text.replace(eng, per)
    return text


def _format_rials(value) -> str:
    """Format a Rial amount with thousand separators in Persian digits, or '-' when absent."""
    if value is None:
        return "-"
    return _to_persian_digits(f"{value:,.0f}")


def _fetch_employer_balance(employer_code: str, funding_year: int) -> float | None:
    """Fetch an employer's current real balance for a funding year.

    Reflects every ``Draft``/``Final`` payment already on record (including
    drafts staged earlier in this same batch), so this is genuinely the
    balance "up to this moment" — not a stale snapshot.
    """
    try:
        response = requests.get(
            f"{API_URL}/employers/{employer_code}/balance",
            params={"funding_year": funding_year},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()["total_balance"]
        st.error(f"❌ خطا در دریافت موجودی کارفرما: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت موجودی کارفرما: {exc}")
    return None


def _response_detail(response: requests.Response) -> str:
    """Extract a user-facing API error detail from JSON or text responses."""
    try:
        response_data = response.json()
    except ValueError:
        response_data = None

    if isinstance(response_data, dict):
        detail = response_data.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail
        if isinstance(detail, list):
            messages = [
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            ]
            return " ".join(messages)
    elif isinstance(response_data, str) and response_data.strip():
        return response_data

    return f"خطا در پردازش درخواست (کد وضعیت: {response.status_code})."


def _fetch_drafts(series: str) -> list[dict] | None:
    """Fetch active drafts for a series, handling connection errors gracefully."""
    try:
        response = requests.get(
            f"{API_URL}/payments/drafts", params={"series": series}, timeout=5
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"❌ خطا در دریافت لیست پیش‌نویس‌ها: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت لیست پیش‌نویس‌ها: {exc}")
    return None


def _to_persian_row(item: dict) -> dict:
    """Map one enriched payment record onto the exact required headers."""
    return {
        "کد رهگیری پرداخت": item["tracking_code"],
        "کد قرارداد": item["contract_tracking_code"],
        "متقاضی": item.get("employer_name") or "-",
        "دانشگاه یا موسسه مجری": item.get("university_name") or "-",
        "عنوان قرارداد": item.get("contract_title") or "-",
        "مبلغ قرارداد (ریال)": item.get("contract_total_amount"),
        "مبلغ پرداختی (ریال)": item["amount"],
        "پرداخت از محل سال مالی": item["funding_year"],
        "مانده متقاضی (ریال)": item.get("employer_balance_after"),
    }


def _build_dataframe(items: list[dict]) -> pd.DataFrame:
    """Build the exact-header DataFrame shared by the table and the export."""
    rows = [_to_persian_row(item) for item in items]
    return pd.DataFrame(rows, columns=DRAFT_TABLE_COLUMNS)


def _display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format numeric columns with Persian digits for on-screen display.

    Raw numbers stay in the Excel export (unaffected by this function).
    Tracking-code columns are deliberately left untouched — those are
    system identifiers, not display quantities, and must stay
    byte-for-byte matchable against the database.
    """
    display_df = df.copy()
    for column in NUMERIC_TABLE_COLUMNS:
        display_df[column] = display_df[column].apply(_format_rials)
    display_df["پرداخت از محل سال مالی"] = display_df["پرداخت از محل سال مالی"].apply(
        _to_persian_digits
    )
    return display_df


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert the drafts/finalized DataFrame to an in-memory Excel file."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Payments")
    output.seek(0)
    return output.getvalue()


def _apply_pending_row_reset() -> None:
    """Clear the just-added row's widget state before the widgets are recreated."""
    if not st.session_state.pop("batch_row_reset_pending", False):
        return
    for widget_key in ROW_RESET_KEYS:
        st.session_state.pop(widget_key, None)


def _schedule_row_reset() -> None:
    st.session_state.batch_row_reset_pending = True
    st.rerun()


_apply_pending_row_reset()

# st.success() is an ephemeral inline element cleared by an immediately
# following st.rerun() — unlike st.toast(), it does not survive into the
# next run. Both the "row added" balance message and the finalize message
# are therefore stashed in session_state and rendered once, here, right
# after the rerun that follows a successful action.
add_success_message = st.session_state.pop("batch_add_success_message", None)
if add_success_message:
    st.success(add_success_message)

finalize_success_message = st.session_state.pop("batch_finalize_success_message", None)
if finalize_success_message:
    st.success(finalize_success_message)


# ─── Finalized "success state": Excel download, entry UI hidden ──────────
finalize_state = st.session_state.get(FINALIZE_STATE_KEY)
if finalize_state:
    st.download_button(
        label="📥 دانلود فایل اکسل لیست پرداخت",
        data=finalize_state["excel_bytes"],
        file_name=finalize_state["filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    st.markdown("---")
    st.table(_display_dataframe(finalize_state["dataframe"]).reset_index(drop=True))
    if st.button("🆕 شروع لیست پرداخت جدید"):
        st.session_state.pop(FINALIZE_STATE_KEY, None)
        st.rerun()
    st.stop()


# ─── 1. Global Config: applies to every new row added below ──────────────
st.subheader("۱. اطلاعات کلی لیست پرداخت")
col_s1, col_s2 = st.columns(2)
with col_s1:
    series_number = st.text_input(
        "شماره سری پرداخت (لیست):", value="15", key="batch_series"
    )
with col_s2:
    payment_year = st.number_input(
        "سال پرداخت (شمسی):",
        min_value=1398,
        max_value=1410,
        value=1405,
        key="batch_payment_year",
    )

st.markdown("---")

# ─── 2. Add New Row: search a contract, then stage a draft against it ────
st.subheader("۲. ورود اطلاعات ردیف جدید")

search_query = st.text_input(
    "🔍 جستجوی قرارداد (کد رهگیری یا بخشی از عنوان قرارداد):",
    key="batch_search_query",
)
selected_contract = None

if search_query:
    try:
        response = requests.get(
            f"{API_URL}/contracts/search", params={"q": search_query}, timeout=5
        )
        if response.status_code == 200 and response.json():
            contracts_found = response.json()
            options = {
                f"{c['contract_tracking_code']} - {c['title'][:40]}...": c
                for c in contracts_found
            }
            choice = st.selectbox(
                "قرارداد مورد نظر را انتخاب کنید:",
                list(options.keys()),
                key="batch_contract_choice",
            )
            selected_contract = options[choice]
            st.success(
                f"🏢 متقاضی (شرکت مادر): {selected_contract['employer_name']} | "
                f"🎓 مجری: {selected_contract['university_name']} | "
                f"🧑‍💻 فناور: {selected_contract['researcher_name']}"
            )

            # Live balance preview: the funding-year widget below hasn't run
            # yet this script pass, so its *previous* value (or the default,
            # on first selection) is read straight from session_state — the
            # same value that widget is about to render with.
            preview_funding_year = st.session_state.get("batch_funding_year", 1402)
            preview_balance = _fetch_employer_balance(
                selected_contract["employer_classification_code"], preview_funding_year
            )
            if preview_balance is not None:
                st.info(
                    f"💰 موجودی فعلی کارفرما تا این لحظه (سال مالی "
                    f"{_to_persian_digits(preview_funding_year)}): "
                    f"{_format_rials(preview_balance)} ریال"
                )
        else:
            st.warning("هیچ قراردادی با این مشخصات یافت نشد.")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطا در اتصال به بک‌اند: {exc}")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    pay_tracking_code = st.text_input(
        "کد رهگیری پرداخت (از سامانه ساتع):", key="batch_pay_tracking_code"
    )
with col_r2:
    # Integer-only amount: value/step are ints, which puts st.number_input
    # into integer mode (it returns a float if any of value/step/min/max
    # were floats), and format="%d" keeps the on-screen display integral.
    amount = st.number_input(
        "مبلغ پرداختی (ریال):",
        min_value=0,
        step=1000000,
        format="%d",
        value=0,
        key="batch_amount",
    )
with col_r3:
    funding_year = st.number_input(
        "پرداخت از محل سال مالی (شمسی):",
        min_value=1398,
        max_value=1410,
        value=1402,
        key="batch_funding_year",
    )

if st.button("➕ افزودن به لیست", type="primary"):
    if not selected_contract or not pay_tracking_code.strip() or amount <= 0:
        st.error("لطفاً تمامی فیلدهای الزامی ردیف را تکمیل کنید.")
    elif not series_number.strip():
        st.error("لطفاً شماره سری پرداخت را وارد کنید.")
    else:
        draft_payload = {
            "tracking_code": pay_tracking_code.strip(),
            "contract_tracking_code": selected_contract["contract_tracking_code"],
            "amount": int(amount),
            "funding_year": int(funding_year),
            "payment_year": int(payment_year),
            "series": series_number.strip(),
        }
        try:
            draft_response = requests.post(
                f"{API_URL}/payments/draft", json=draft_payload, timeout=10
            )
            if draft_response.status_code == 201:
                data = draft_response.json()
                st.session_state.batch_add_success_message = (
                    "✅ پرداخت به لیست اضافه شد. "
                    f"مانده کارفرما قبل از پرداخت: {_format_rials(data['employer_balance_before'])} ریال "
                    f"| مانده پس از پرداخت: {_format_rials(data['employer_balance_after'])} ریال"
                )
                _schedule_row_reset()
            elif draft_response.status_code == 400:
                # Insufficient funds or duplicate tracking code — the exact
                # backend message (deficit amount, etc.) is shown verbatim.
                st.error(f"❌ {_response_detail(draft_response)}")
            else:
                st.error(f"❌ خطا در افزودن ردیف: {_response_detail(draft_response)}")
        except requests.exceptions.ConnectionError:
            st.error(
                "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
            )
        except requests.exceptions.Timeout:
            st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
        except Exception as exc:
            st.error(f"خطا در ارتباط با سرور: {exc}")

st.markdown("---")

# ─── 3. Data Table: always reflects the database, not local state ────────
st.subheader("۳. لیست پیش‌نویس پرداخت‌های در حال انتظار (ثبت‌شده در پایگاه داده)")

current_series = series_number.strip()
drafts = _fetch_drafts(current_series) if current_series else None

if drafts:
    drafts_df = _build_dataframe(drafts)
    st.table(_display_dataframe(drafts_df).reset_index(drop=True))

    delete_col1, delete_col2 = st.columns([3, 1])
    with delete_col1:
        delete_options = {
            f"{d['tracking_code']} — {d.get('employer_name') or '-'} "
            f"({_format_rials(d['amount'])} ریال)": d["tracking_code"]
            for d in drafts
        }
        delete_choice = st.selectbox(
            "حذف یک ردیف از لیست:", list(delete_options.keys()), key="batch_delete_choice"
        )
    with delete_col2:
        st.write("")
        st.write("")
        if st.button("🗑️ حذف ردیف انتخاب‌شده"):
            tracking_code_to_delete = delete_options[delete_choice]
            try:
                delete_response = requests.delete(
                    f"{API_URL}/payments/draft/{tracking_code_to_delete}", timeout=10
                )
                if delete_response.status_code == 200:
                    st.toast("🗑️ ردیف حذف شد.", icon="🗑️")
                    st.rerun()
                else:
                    st.error(f"❌ خطا در حذف ردیف: {_response_detail(delete_response)}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                    "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                )
            except Exception as exc:
                st.error(f"خطا در حذف ردیف: {exc}")

    st.markdown("### 🚀 نهایی‌سازی و ثبت در دیتابیس")
    if st.button("💾 تأیید نهایی لیست", type="primary"):
        try:
            finalize_response = requests.post(
                f"{API_URL}/payments/finalize-batch",
                json={"series": current_series},
                timeout=10,
            )
            if finalize_response.status_code == 200:
                data = finalize_response.json()
                finalized_df = _build_dataframe(data["finalized_payments"])
                st.session_state[FINALIZE_STATE_KEY] = {
                    "excel_bytes": _to_excel_bytes(finalized_df),
                    "filename": f"payments_series_{current_series}.xlsx",
                    "dataframe": finalized_df,
                }
                st.session_state.batch_finalize_success_message = (
                    f"🎉 لیست با موفقیت نهایی شد! {data['finalized_count']} "
                    "قلم پرداخت ثبت و قفل گردید."
                )
                st.rerun()
            else:
                st.error(f"❌ خطا در نهایی‌سازی: {_response_detail(finalize_response)}")
        except requests.exceptions.ConnectionError:
            st.error(
                "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
            )
        except Exception as exc:
            st.error(f"خطا در ارسال نهایی به سرور: {exc}")
elif drafts is not None:
    st.info(
        "لیست پیش‌نویس برای این سری در حال حاضر خالی است. "
        "ردیف‌های پرداخت را از بخش بالا اضافه کنید."
    )
