"""Render the Phase 4 contract registration form."""

import re
from pathlib import Path
from uuid import uuid4

import requests
import streamlit as st

from core.date_helper import parse_strict_jalali_iso

API_URL = "http://127.0.0.1:8000/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ARCHIVE_DIR = PROJECT_ROOT / "data" / "Archive" / "Contracts"
ALLOWED_ATTACHMENT_TYPES = {"pdf", "jpg", "jpeg", "png"}
FORM_KEY = "contract_entry_form"
FORM_WIDGET_KEYS = (
    "contract_employer",
    "contract_university",
    "contract_researcher",
    "contract_tracking_code",
    "contract_number",
    "contract_proposal_id",
    "contract_title",
    "contract_total_amount",
    "contract_duration_months",
    "contract_date",
    "contract_attachment",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox,
    .stDateInput, .stFileUploader, p, div {
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

st.title("📄 فرم ثبت قرارداد جدید")


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


def _optional_text(value: str) -> str | None:
    """Return stripped optional form text or ``None`` when empty."""
    normalized_value = value.strip()
    return normalized_value or None


def _safe_filename(original_name: str) -> str:
    """Create a collision-resistant filename without unsafe path characters."""
    original_path = Path(original_name)
    extension = original_path.suffix.lower()
    sanitized_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", original_path.stem).strip("_")
    safe_stem = sanitized_stem[:80] or "contract"
    return f"{safe_stem}_{uuid4().hex}{extension}"


def _save_attachment(uploaded_file) -> Path | None:
    """Save an uploaded contract document and return its project-relative path."""
    if uploaded_file is None:
        return None

    extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_ATTACHMENT_TYPES:
        raise ValueError("نوع فایل نامعتبر است. فقط PDF، JPG و PNG مجاز هستند.")

    CONTRACT_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    destination = CONTRACT_ARCHIVE_DIR / _safe_filename(uploaded_file.name)
    destination.write_bytes(uploaded_file.getvalue())
    return destination.relative_to(PROJECT_ROOT)


def _delete_attachment(relative_path: Path | None) -> None:
    """Remove a newly saved attachment after a failed contract submission."""
    if relative_path is None:
        return
    absolute_path = (PROJECT_ROOT / relative_path).resolve()
    archive_root = CONTRACT_ARCHIVE_DIR.resolve()
    if archive_root not in absolute_path.parents:
        return
    absolute_path.unlink(missing_ok=True)


def _schedule_form_reset() -> None:
    """Schedule widget cleanup for the next Streamlit render cycle."""
    st.session_state.contract_form_reset_pending = True
    st.rerun()


def _apply_pending_form_reset() -> None:
    """Clear contract widget state before the widgets are recreated."""
    if not st.session_state.pop("contract_form_reset_pending", False):
        return
    for widget_key in FORM_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)


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

    return f"خطا در ثبت قرارداد (کد وضعیت: {response.status_code})."


_apply_pending_form_reset()

employers = _safe_lookup("/employers/lookup")
universities = _safe_lookup("/universities/lookup")
researchers = _safe_lookup("/researchers/lookup")

if not employers or not universities or not researchers:
    st.warning(
        "برای ادامه، ابتدا باید حداقل یک کارفرما (غیر زیرمجموعه)، "
        "یک دانشگاه و یک فناور در سیستم موجود باشد."
    )
    st.stop()

success_message = st.session_state.pop("contract_success_message", None)
if success_message:
    st.success(success_message)
    st.toast("✅ قرارداد جدید ثبت شد.", icon="📄")

employer_options = {
    item["classification_code"]: _format_option(item, "classification_code")
    for item in employers
}
university_options = {
    item["national_id"]: _format_option(item, "national_id")
    for item in universities
}
researcher_options = {
    item["national_id"]: _format_option(item, "national_id")
    for item in researchers
}

with st.form(FORM_KEY, clear_on_submit=False):
    st.subheader("۱. اطلاعات طرف‌های قرارداد")
    employer_choice = st.selectbox(
        "🏢 کارفرما (شرکت مادر):",
        options=list(employer_options),
        format_func=employer_options.get,
        key="contract_employer",
    )
    university_choice = st.selectbox(
        "🎓 مجری (دانشگاه/موسسه):",
        options=list(university_options),
        format_func=university_options.get,
        key="contract_university",
    )
    researcher_choice = st.selectbox(
        "🧑‍💻 فناور (مجری پروژه):",
        options=list(researcher_options),
        format_func=researcher_options.get,
        key="contract_researcher",
    )

    st.markdown("---")
    st.subheader("۲. مشخصات قرارداد")
    tracking_code = st.text_input(
        "🔖 کد رهگیری قرارداد:", key="contract_tracking_code"
    )

    identifier_col, proposal_col = st.columns(2)
    with identifier_col:
        contract_number = st.text_input(
            "📑 شماره قرارداد:", key="contract_number"
        )
    with proposal_col:
        proposal_id = st.text_input(
            "🧾 شناسه پیشنهاده:", key="contract_proposal_id"
        )

    title = st.text_input("📝 عنوان قرارداد:", key="contract_title")
    amount_col, duration_col = st.columns(2)
    with amount_col:
        total_amount = st.number_input(
            "💰 مبلغ کل قرارداد (ریال):",
            min_value=0.0,
            step=1_000_000.0,
            format="%.2f",
            key="contract_total_amount",
        )
    with duration_col:
        duration_months = st.number_input(
            "⏳ مدت قرارداد (ماه):",
            min_value=1,
            step=1,
            value=12,
            key="contract_duration_months",
        )

    contract_date_str = st.text_input(
        "📅 تاریخ انعقاد قرارداد (شمسی):",
        placeholder="مثال: 1403/05/12",
        key="contract_date",
    )
    attachment = st.file_uploader(
        "📎 فایل قرارداد (PDF/JPG/PNG):",
        type=sorted(ALLOWED_ATTACHMENT_TYPES),
        key="contract_attachment",
    )
    submitted = st.form_submit_button("✅ ثبت قرارداد", type="primary")

if submitted:
    if not tracking_code.strip() or not title.strip():
        st.error("لطفاً کد رهگیری و عنوان قرارداد را تکمیل کنید.")
    elif total_amount <= 0:
        st.error("مبلغ قرارداد باید بیشتر از صفر باشد.")
    else:
        try:
            contract_date_iso = parse_strict_jalali_iso(contract_date_str)
        except ValueError:
            st.warning(
                "تاریخ نامعتبر است. بررسی کنید که روز و ماه با تقویم شمسی "
                "تطابق داشته باشد."
            )
        else:
            attachment_path = None
            try:
                attachment_path = _save_attachment(attachment)
                payload = {
                    "tracking_code": tracking_code.strip(),
                    "employer_classification_code": employer_choice,
                    "university_national_id": university_choice,
                    "researcher_national_id": researcher_choice,
                    "contract_number": _optional_text(contract_number),
                    "proposal_id": _optional_text(proposal_id),
                    "attachment_path": (
                        attachment_path.as_posix() if attachment_path else None
                    ),
                    "title": title.strip(),
                    "total_amount": float(total_amount),
                    "contract_date": contract_date_iso,
                    "duration_months": int(duration_months),
                }
                response = requests.post(
                    f"{API_URL}/contracts/", json=payload, timeout=10
                )
                if response.status_code == 201:
                    data = response.json()
                    st.session_state.contract_success_message = (
                        "🎉 قرارداد با موفقیت ثبت شد. "
                        f"کد: {data.get('contract_tracking_code')} | "
                        f"کارفرما: {data.get('employer_name')} | "
                        f"دانشگاه: {data.get('university_name')} | "
                        f"فناور: {data.get('researcher_name')}"
                    )
                    _schedule_form_reset()
                else:
                    _delete_attachment(attachment_path)
                    st.error(f"❌ خطا در ثبت قرارداد: {_response_detail(response)}")
            except ValueError as exc:
                _delete_attachment(attachment_path)
                st.error(str(exc))
            except requests.exceptions.ConnectionError:
                _delete_attachment(attachment_path)
                st.error(
                    "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                    "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                )
            except requests.exceptions.Timeout:
                _delete_attachment(attachment_path)
                st.error("خطا: پاسخ سرور بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except OSError as exc:
                _delete_attachment(attachment_path)
                st.error(f"خطا در ذخیره فایل قرارداد: {exc}")
            except Exception as exc:
                _delete_attachment(attachment_path)
                st.error(f"خطا در ارسال اطلاعات به سرور: {exc}")
