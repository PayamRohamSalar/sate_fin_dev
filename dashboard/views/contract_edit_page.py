"""Render the contract search-and-edit form (Phase 4 follow-up)."""

from datetime import date

import jdatetime
import requests
import streamlit as st

from core.date_helper import parse_strict_jalali_iso

API_URL = "http://127.0.0.1:8000/api/v1"
SELECTED_TRACKING_CODE_KEY = "contract_edit_selected_tracking_code"
LOADED_DETAIL_KEY = "contract_edit_loaded_detail"
LOAD_SEQ_KEY = "contract_edit_load_seq"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox,
    .stDateInput, p, div {
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

st.title("✏️ جستجو و ویرایش قرارداد")


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


def _fetch_contract_detail(tracking_code: str) -> dict | None:
    """Fetch full contract details for editing, handling errors gracefully."""
    try:
        response = requests.get(
            f"{API_URL}/contracts/{tracking_code}", timeout=5
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"❌ خطا در دریافت اطلاعات قرارداد: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت اطلاعات قرارداد: {exc}")
    return None


def _gregorian_iso_to_jalali_str(iso_date: str | None) -> str:
    """Convert a Gregorian ISO date string to a Jalali ``YYYY/MM/DD`` string."""
    if not iso_date:
        return ""
    gregorian_date = date.fromisoformat(iso_date)
    return jdatetime.date.fromgregorian(date=gregorian_date).strftime("%Y/%m/%d")


def _index_of(options: list[str], current_value: str | None) -> int:
    """Return the dropdown index for the contract's current FK value.

    Falls back to ``0`` (and a warning) if the stored value is somehow
    absent from the active lookup — e.g. the linked record was soft-deleted
    after the contract was created.
    """
    if current_value in options:
        return options.index(current_value)
    return 0


employers = _safe_lookup("/employers/lookup")
universities = _safe_lookup("/universities/lookup")
researchers = _safe_lookup("/researchers/lookup")

if not employers or not universities or not researchers:
    st.warning(
        "برای ادامه، ابتدا باید حداقل یک کارفرما (غیر زیرمجموعه)، "
        "یک دانشگاه و یک فناور در سیستم موجود باشد."
    )
    st.stop()

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

success_message = st.session_state.pop("contract_edit_success_message", None)
if success_message:
    st.success(success_message)
    st.toast("✅ قرارداد با موفقیت ویرایش شد.", icon="✏️")

# ─── 1. Search ───────────────────────────────────────────────────────────
st.subheader("۱. جستجوی قرارداد")
search_query = st.text_input(
    "🔍 جستجو بر اساس کد رهگیری یا عنوان قرارداد:",
    key="contract_edit_search_query",
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
                f"{c['contract_tracking_code']} - {c['title'][:40]}": c
                for c in contracts_found
            }
            choice = st.selectbox(
                "قرارداد مورد نظر برای ویرایش را انتخاب کنید:",
                list(options.keys()),
                key="contract_edit_search_choice",
            )
            selected_contract = options[choice]
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
        st.error(f"خطا در جستجوی قرارداد: {exc}")

# ─── 2. Load full details once a contract is selected ───────────────────
if selected_contract is not None:
    tracking_code = selected_contract["contract_tracking_code"]
    if st.session_state.get(SELECTED_TRACKING_CODE_KEY) != tracking_code:
        detail = _fetch_contract_detail(tracking_code)
        if detail is not None:
            st.session_state[SELECTED_TRACKING_CODE_KEY] = tracking_code
            st.session_state[LOADED_DETAIL_KEY] = detail
            # Bump the load sequence so widget keys below are unique per
            # fetch, not just per tracking_code. Without this, re-editing
            # the *same* contract again later in one browser session would
            # reuse Streamlit's cached widget state from the previous edit
            # instead of the freshly fetched values, since a widget's
            # `value=`/`index=` argument is ignored once its key already
            # has an entry in session_state.
            st.session_state[LOAD_SEQ_KEY] = (
                st.session_state.get(LOAD_SEQ_KEY, 0) + 1
            )

detail = st.session_state.get(LOADED_DETAIL_KEY)

# ─── 3. Pre-filled edit form ─────────────────────────────────────────────
if detail is not None:
    tracking_code = detail["tracking_code"]
    form_instance_key = f"{tracking_code}_{st.session_state.get(LOAD_SEQ_KEY, 0)}"
    st.markdown("---")
    st.subheader(f"۲. ویرایش قرارداد: {tracking_code}")

    # Widget keys are namespaced per (tracking_code, load sequence) so both
    # switching to a different contract AND reloading the same contract
    # again create fresh widgets pre-filled with the newly loaded values.
    with st.form(f"contract_edit_form_{form_instance_key}", clear_on_submit=False):
        st.markdown("**۱. اطلاعات طرف‌های قرارداد**")
        employer_keys = list(employer_options)
        university_keys = list(university_options)
        researcher_keys = list(researcher_options)

        employer_choice = st.selectbox(
            "🏢 کارفرما (شرکت مادر):",
            options=employer_keys,
            format_func=employer_options.get,
            index=_index_of(
                employer_keys, detail["employer_classification_code"]
            ),
            key=f"edit_employer_{form_instance_key}",
        )
        university_choice = st.selectbox(
            "🎓 مجری (دانشگاه/موسسه):",
            options=university_keys,
            format_func=university_options.get,
            index=_index_of(
                university_keys, detail["university_national_id"]
            ),
            key=f"edit_university_{form_instance_key}",
        )
        researcher_choice = st.selectbox(
            "🧑‍💻 فناور (مجری پروژه):",
            options=researcher_keys,
            format_func=researcher_options.get,
            index=_index_of(
                researcher_keys, detail["researcher_national_id"]
            ),
            key=f"edit_researcher_{form_instance_key}",
        )

        st.markdown("---")
        st.markdown("**۲. مشخصات قرارداد**")

        identifier_col, proposal_col = st.columns(2)
        with identifier_col:
            contract_number = st.text_input(
                "📑 شماره قرارداد:",
                value=detail.get("contract_number") or "",
                key=f"edit_contract_number_{form_instance_key}",
            )
        with proposal_col:
            proposal_id = st.text_input(
                "🧾 شناسه پیشنهاده:",
                value=detail.get("proposal_id") or "",
                key=f"edit_proposal_id_{form_instance_key}",
            )

        title = st.text_input(
            "📝 عنوان قرارداد:",
            value=detail["title"],
            key=f"edit_title_{form_instance_key}",
        )

        amount_col, duration_col = st.columns(2)
        with amount_col:
            total_amount = st.number_input(
                "💰 مبلغ کل قرارداد (ریال):",
                min_value=0.0,
                step=1_000_000.0,
                format="%.2f",
                value=float(detail["total_amount"]),
                key=f"edit_total_amount_{form_instance_key}",
            )
        with duration_col:
            duration_months = st.number_input(
                "⏳ مدت قرارداد (ماه):",
                min_value=1,
                step=1,
                value=int(detail.get("duration_months") or 1),
                key=f"edit_duration_months_{form_instance_key}",
            )

        contract_date_str = st.text_input(
            "📅 تاریخ انعقاد قرارداد (شمسی):",
            value=_gregorian_iso_to_jalali_str(detail.get("contract_date")),
            placeholder="مثال: 1403/05/12",
            key=f"edit_contract_date_{form_instance_key}",
        )

        if detail.get("attachment_path"):
            st.caption(f"📎 فایل پیوست فعلی: {detail['attachment_path']}")
        else:
            st.caption("📎 هیچ فایل پیوستی برای این قرارداد ثبت نشده است.")

        submitted = st.form_submit_button("💾 ذخیره تغییرات", type="primary")

    if submitted:
        if not title.strip():
            st.error("لطفاً عنوان قرارداد را تکمیل کنید.")
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
                payload = {
                    "employer_classification_code": employer_choice,
                    "university_national_id": university_choice,
                    "researcher_national_id": researcher_choice,
                    "contract_number": _optional_text(contract_number),
                    "proposal_id": _optional_text(proposal_id),
                    "attachment_path": detail.get("attachment_path"),
                    "title": title.strip(),
                    "total_amount": int(total_amount),
                    "contract_date": contract_date_iso,
                    "duration_months": int(duration_months),
                }
                try:
                    response = requests.put(
                        f"{API_URL}/contracts/{tracking_code}",
                        json=payload,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.contract_edit_success_message = (
                            "🎉 قرارداد با موفقیت ویرایش شد. "
                            f"کد: {data.get('contract_tracking_code')} | "
                            f"کارفرما: {data.get('employer_name')} | "
                            f"دانشگاه: {data.get('university_name')} | "
                            f"فناور: {data.get('researcher_name')}"
                        )
                        # Clear loaded state so the page returns to search.
                        st.session_state.pop(SELECTED_TRACKING_CODE_KEY, None)
                        st.session_state.pop(LOADED_DETAIL_KEY, None)
                        st.rerun()
                    else:
                        st.error(
                            f"❌ خطا در ذخیره تغییرات: {_response_detail(response)}"
                        )
                except requests.exceptions.ConnectionError:
                    st.error(
                        "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن "
                        "شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                    )
                except requests.exceptions.Timeout:
                    st.error(
                        "خطا: پاسخ سرور بیش از حد طول کشید. لطفاً مجدداً تلاش کنید."
                    )
                except Exception as exc:
                    st.error(f"خطا در ارسال اطلاعات به سرور: {exc}")
elif search_query and selected_contract is None:
    st.info("قراردادی را از نتایج جستجو انتخاب کنید تا فرم ویرایش نمایش داده شود.")
