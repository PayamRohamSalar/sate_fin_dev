"""Render the trustee (custodial) payment registration form (فرم ثبت پرداخت‌های امانی).

A trustee payment is a disbursement paid directly by the executing
university/institution out of its own funds, outside SATE's budget pool --
recorded purely for contract-status reconciliation. ``contract_tracking_code``
and ``employer_code`` are informational only (not foreign keys), so this form
accepts a contract found via search *or* one typed in manually when the
source reconciliation data doesn't match anything already in the system.
"""

import logging

import requests
import streamlit as st

from core.date_helper import parse_strict_jalali_iso

API_URL = "http://127.0.0.1:8000/api/v1"
FORM_KEY = "trustee_payment_form"
FORM_WIDGET_KEYS = (
    "trustee_search_query",
    "trustee_contract_choice",
    "trustee_manual_mode",
    "trustee_manual_contract_code",
    "trustee_manual_employer",
    "trustee_tracking_code",
    "trustee_amount",
    "trustee_payment_year",
    "trustee_notification_number",
    "trustee_notification_date",
    "trustee_source_note",
)

logger = logging.getLogger(__name__)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox,
    .stTextArea, .stCheckbox, .stDateInput, p, div {
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

st.title("🏦 فرم ثبت پرداخت‌های امانی")
st.caption(
    "پرداخت‌هایی که مستقیماً توسط دانشگاه/موسسه مجری از محل منابع خود انجام "
    "شده‌اند و خارج از استخر بودجه مدیریت‌شده توسط صندوق ثبت می‌شوند. این "
    "رکوردها صرفاً برای تطبیق وضعیت قرارداد هستند و در هیچ محاسبه مانده مالی "
    "کارفرما لحاظ نمی‌شوند."
)


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

    return f"خطا در ثبت پرداخت امانی (کد وضعیت: {response.status_code})."


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


def _format_rials(amount) -> str:
    """Format a numeric amount with thousand separators and a Rial suffix."""
    return f"{amount:,.0f} ریال"


def _schedule_form_reset() -> None:
    """Schedule widget cleanup for the next Streamlit render cycle."""
    st.session_state.trustee_form_reset_pending = True
    st.rerun()


def _apply_pending_form_reset() -> None:
    """Clear trustee-payment widget state before the widgets are recreated."""
    if not st.session_state.pop("trustee_form_reset_pending", False):
        return
    for widget_key in FORM_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)


_apply_pending_form_reset()

success_message = st.session_state.pop("trustee_success_message", None)
if success_message:
    st.success(success_message)
    st.toast("✅ پرداخت امانی جدید ثبت شد.", icon="🏦")

st.markdown("---")
st.subheader("۱. مشخص کردن قرارداد مرتبط (اختیاری)")

manual_mode = st.checkbox(
    "قرارداد در سیستم ثبت نشده / کد قرارداد و کارفرما را دستی وارد می‌کنم",
    key="trustee_manual_mode",
)

contract_tracking_code = None
employer_code = None
employer_display_name = None

if manual_mode:
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        contract_tracking_code = st.text_input(
            "کد قرارداد (دستی):", key="trustee_manual_contract_code"
        )
    with col_m2:
        employers = _safe_lookup("/employers/lookup")
        employer_options = {"": "— بدون کارفرما —"}
        employer_options.update(
            {item["classification_code"]: f"{item['classification_code']} - {item['name']}" for item in employers}
        )
        employer_choice = st.selectbox(
            "کارفرما (اختیاری):",
            options=list(employer_options),
            format_func=employer_options.get,
            key="trustee_manual_employer",
        )
        employer_code = employer_choice or None
else:
    search_query = st.text_input(
        "🔍 جستجوی قرارداد (کد رهگیری یا بخشی از عنوان قرارداد):",
        key="trustee_search_query",
    )
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
                    key="trustee_contract_choice",
                )
                selected_contract = options[choice]
                contract_tracking_code = selected_contract["contract_tracking_code"]
                employer_code = selected_contract["employer_classification_code"]
                employer_display_name = selected_contract["employer_name"]
                st.success(
                    f"🏢 کارفرما: {selected_contract['employer_name']} | "
                    f"🎓 مجری: {selected_contract['university_name']} | "
                    f"🧑‍💻 فناور: {selected_contract['researcher_name']}"
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

st.markdown("---")
st.subheader("۲. اطلاعات پرداخت امانی")

with st.form(FORM_KEY, clear_on_submit=False):
    tracking_code = st.text_input(
        "کد رهگیری پرداخت امانی (از فایل منبع):", key="trustee_tracking_code"
    )
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        amount = st.number_input(
            "مبلغ پرداختی (ریال):",
            min_value=0,
            step=1_000_000,
            format="%d",
            value=0,
            key="trustee_amount",
        )
    with col_r2:
        payment_year = st.number_input(
            "سال پرداخت (شمسی):",
            min_value=1398,
            max_value=1410,
            value=1405,
            step=1,
            key="trustee_payment_year",
        )
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        notification_number = st.text_input(
            "شماره نامه ابلاغ (اختیاری):", key="trustee_notification_number"
        )
    with col_n2:
        notification_date = st.text_input(
            "📅 تاریخ نامه ابلاغ (شمسی، اختیاری):",
            placeholder="مثال: 1405/03/01",
            key="trustee_notification_date",
        )
    source_note = st.text_area(
        "توضیحات/منبع سند (اختیاری):",
        placeholder="مثال: صورت تطبیق دانشگاه الف - مرداد ۱۴۰۵",
        key="trustee_source_note",
    )
    submitted = st.form_submit_button("✅ ثبت پرداخت امانی", type="primary")

if submitted:
    if not tracking_code.strip():
        st.error("لطفاً کد رهگیری پرداخت امانی را وارد کنید.")
    elif amount <= 0:
        st.error("مبلغ پرداختی باید بیشتر از صفر باشد.")
    else:
        parsed_notification_date = None
        date_is_valid = True
        if notification_date.strip():
            try:
                parsed_notification_date = parse_strict_jalali_iso(notification_date)
            except ValueError:
                date_is_valid = False
                st.error(
                    "تاریخ نامه ابلاغ نامعتبر است. بررسی کنید که روز و ماه با "
                    "تقویم شمسی تطابق داشته باشد (مثال: 1405/03/01)."
                )

        if date_is_valid:
            payload = {
                "tracking_code": tracking_code.strip(),
                "contract_tracking_code": contract_tracking_code,
                "employer_code": employer_code,
                "amount": int(amount),
                "payment_year": int(payment_year),
                "notification_letter_number": notification_number.strip() or None,
                "notification_date": parsed_notification_date,
                "source_note": source_note.strip() or None,
            }
            try:
                response = requests.post(
                    f"{API_URL}/trustee-payments/", json=payload, timeout=15
                )
                if response.status_code == 201:
                    data = response.json()
                    success_text = (
                        "🎉 پرداخت امانی با موفقیت ثبت شد. "
                        f"کد رهگیری: {data.get('tracking_code')} | "
                        f"مبلغ: {_format_rials(data.get('amount', 0))}"
                    )
                    if data.get("contract_tracking_code"):
                        success_text += f" | قرارداد: {data['contract_tracking_code']}"
                    if data.get("employer_name") or employer_display_name:
                        success_text += (
                            f" | کارفرما: {data.get('employer_name') or employer_display_name}"
                        )
                    st.session_state.trustee_success_message = success_text
                    logger.info(
                        "Trustee payment registered: tracking_code=%s amount=%s",
                        tracking_code,
                        amount,
                    )
                    _schedule_form_reset()
                else:
                    st.error(f"❌ خطا در ثبت پرداخت امانی: {_response_detail(response)}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                    "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                )
            except requests.exceptions.Timeout:
                st.error("خطا: پاسخ سرور بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except Exception as exc:
                st.error(f"خطا در ارسال اطلاعات به سرور: {exc}")
