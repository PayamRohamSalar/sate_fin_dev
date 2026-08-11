"""Render the employer deposit registration form (فرم ثبت واریزی شرکت‌ها)."""

import logging

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/v1"
ALLOWED_RECEIPT_TYPES = {"pdf", "jpg", "jpeg", "png"}
FORM_KEY = "deposit_entry_form"
FORM_WIDGET_KEYS = (
    "deposit_employer",
    "deposit_fiscal_year",
    "deposit_amount",
    "deposit_description",
    "deposit_receipt",
)

logger = logging.getLogger(__name__)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox,
    .stFileUploader, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="InputInstructions"] { display: none !important; }
    h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
    h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
    hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💰 فرم ثبت واریزی شرکت‌ها")


def _safe_lookup(path: str) -> list[dict]:
    """Fetch a lookup list and display a localized error when unavailable."""
    try:
        response = requests.get(f"{API_URL}{path}", timeout=5)
        if response.status_code == 200:
            return response.json()
        st.error(f"خطا در دریافت اطلاعات ({path}): {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت اطلاعات: {exc}")
    return []


def _format_option(item: dict, value_key: str) -> str:
    """Format lookup entries as a human-readable code and name pair."""
    return f"{item[value_key]} - {item['name']}"


def _format_rials(amount: float) -> str:
    """Format a numeric amount with thousand separators and a Rial suffix."""
    return f"{amount:,.0f} ریال"


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

    return f"خطا در ثبت واریزی (کد وضعیت: {response.status_code})."


def _fetch_balances(employer_code: str) -> list[dict] | None:
    """Fetch the employer's real-time balances, handling errors gracefully."""
    try:
        response = requests.get(
            f"{API_URL}/deposits/balances/{employer_code}", timeout=10
        )
        if response.status_code == 200:
            return response.json().get("balances", [])
        st.error(f"خطا در دریافت مانده مالی: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت مانده مالی: {exc}")
    return None


def _schedule_form_reset() -> None:
    """Schedule widget cleanup for the next Streamlit render cycle."""
    st.session_state.deposit_form_reset_pending = True
    st.rerun()


def _apply_pending_form_reset() -> None:
    """Clear deposit widget state before the widgets are recreated."""
    if not st.session_state.pop("deposit_form_reset_pending", False):
        return
    for widget_key in FORM_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)


_apply_pending_form_reset()

employers = _safe_lookup("/employers/lookup")
if not employers:
    st.warning(
        "برای ادامه، ابتدا باید حداقل یک کارفرما (غیر زیرمجموعه) در سیستم موجود باشد."
    )
    st.stop()

success_message = st.session_state.pop("deposit_success_message", None)
if success_message:
    st.success(success_message)
    st.toast("✅ واریزی جدید ثبت شد.", icon="💰")

employer_options = {
    item["classification_code"]: _format_option(item, "classification_code")
    for item in employers
}

st.subheader("۱. انتخاب کارفرما")
employer_choice = st.selectbox(
    "🏢 کارفرما:",
    options=list(employer_options),
    format_func=employer_options.get,
    key="deposit_employer",
)

if employer_choice:
    st.markdown("---")
    st.subheader("۲. مانده مالی لحظه‌ای")
    balances = _fetch_balances(employer_choice)
    if balances:
        balance_cols = st.columns(len(balances))
        for col, year_balance in zip(balance_cols, balances):
            with col:
                st.metric(
                    label=f"مانده سال {year_balance['fiscal_year']}",
                    value=_format_rials(year_balance["balance"]),
                )

st.markdown("---")
st.subheader("۳. ثبت واریزی جدید")

with st.form(FORM_KEY, clear_on_submit=False):
    fiscal_year = st.number_input(
        "📅 سال مالی هدف:",
        min_value=1398,
        max_value=1410,
        value=1405,
        step=1,
        key="deposit_fiscal_year",
    )
    deposit_amount = st.number_input(
        "💵 مبلغ واریزی (ریال):",
        min_value=0,
        step=1_000_000,
        value=0,
        key="deposit_amount",
    )
    description = st.text_input(
        "شرح/عنوان واریز (اختیاری):",
        placeholder="مثال: واریزی سه ماهه اول شرکت",
        key="deposit_description",
    )
    receipt_file = st.file_uploader(
        "📎 فیش واریزی (PDF/JPG/PNG):",
        type=sorted(ALLOWED_RECEIPT_TYPES),
        key="deposit_receipt",
    )
    submitted = st.form_submit_button("✅ ثبت واریزی", type="primary")

if submitted:
    if not employer_choice:
        st.error("لطفاً ابتدا یک کارفرما انتخاب کنید.")
    elif deposit_amount <= 0:
        st.error("مبلغ واریزی باید بیشتر از صفر باشد.")
    elif receipt_file is None:
        st.error("لطفاً فیش واریزی را بارگذاری کنید.")
    else:
        try:
            response = requests.post(
                f"{API_URL}/deposits/",
                data={
                    "employer_code": employer_choice,
                    "fiscal_year": int(fiscal_year),
                    "deposit_amount": int(deposit_amount),
                    "description": description.strip() if description else "",
                },
                files={
                    "file": (
                        receipt_file.name,
                        receipt_file.getvalue(),
                        receipt_file.type,
                    )
                },
                timeout=15,
            )
            if response.status_code == 201:
                data = response.json()
                success_text = (
                    "🎉 واریزی با موفقیت ثبت شد. "
                    f"کارفرما: {data.get('employer_name')} | "
                    f"سال مالی: {data.get('fiscal_year')} | "
                    f"مبلغ: {_format_rials(data.get('deposit_amount', 0))}"
                )
                if data.get("description"):
                    success_text += f" | شرح: {data['description']}"
                st.session_state.deposit_success_message = success_text
                logger.info(
                    "Deposit registered: employer=%s year=%s amount=%s",
                    employer_choice,
                    fiscal_year,
                    deposit_amount,
                )
                _schedule_form_reset()
            else:
                st.error(f"❌ خطا در ثبت واریزی: {_response_detail(response)}")
        except requests.exceptions.ConnectionError:
            st.error(
                "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
            )
        except requests.exceptions.Timeout:
            st.error("خطا: پاسخ سرور بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
        except Exception as exc:
            st.error(f"خطا در ارسال اطلاعات به سرور: {exc}")
