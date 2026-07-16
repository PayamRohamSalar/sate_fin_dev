# File: views/contract_entry_page.py
"""Phase 4 - New Contract Registration form."""
import streamlit as st
import requests
import jdatetime


API_URL = "http://127.0.0.1:8000/api/v1"

# ─── Aggressive RTL override + compact Persian theme ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
* { font-family: 'Vazirmatn', sans-serif !important; }
/* Force RTL on main containers and text inputs */
.block-container, .stTextInput, .stNumberInput, .stSelectbox, .stDateInput, p, div {
    direction: rtl !important;
    text-align: right !important;
}
/* Fix sidebar text alignment */
[data-testid="stSidebarNav"] span {
    direction: rtl !important;
    text-align: right !important;
    font-size: 1.05rem !important;
}
/* Compact headers and rules */
h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("📄 فرم ثبت قرارداد جدید")


def _safe_lookup(path: str):
    """Fetch a lookup list, returning [] with a friendly error on failure."""
    try:
        resp = requests.get(f"{API_URL}{path}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"خطا در دریافت اطلاعات ({path}): {resp.status_code}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
        return []
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
        return []
    except Exception as e:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت اطلاعات: {e}")
        return []


employers = _safe_lookup("/employers/lookup")
universities = _safe_lookup("/universities/lookup")
researchers = _safe_lookup("/researchers/lookup")

if not employers or not universities or not researchers:
    st.warning("برای ادامه، ابتدا باید حداقل یک کارفرما (غیر زیرمجموعه)، یک دانشگاه و یک فناور در سیستم موجود باشد.")
    st.stop()


def _format_option(item: dict, value_key: str) -> str:
    return f"{item[value_key]} - {item['name']}"


with st.form("contract_entry_form", clear_on_submit=False):
    st.subheader("۱. اطلاعات طرف‌های قرارداد")

    employer_options = {item["classification_code"]: _format_option(item, "classification_code") for item in employers}
    employer_choice = st.selectbox("🏢 کارفرما (شرکت مادر):", options=list(employer_options.keys()),
                                   format_func=lambda code: employer_options[code])

    university_options = {item["national_id"]: _format_option(item, "national_id") for item in universities}
    university_choice = st.selectbox("🎓 مجری (دانشگاه/موسسه):", options=list(university_options.keys()),
                                     format_func=lambda nid: university_options[nid])

    researcher_options = {item["national_id"]: _format_option(item, "national_id") for item in researchers}
    researcher_choice = st.selectbox("🧑‍💻 فناور (مجری پروژه):", options=list(researcher_options.keys()),
                                     format_func=lambda nid: researcher_options[nid])

    st.markdown("---")
    st.subheader("۲. مشخصات قرارداد")

    tracking_code = st.text_input("🔖 کد رهگیری قرارداد:")
    title = st.text_input("📝 عنوان قرارداد:")

    col1, col2 = st.columns(2)
    with col1:
        total_amount = st.number_input("💰 مبلغ کل قرارداد (ریال):", min_value=0.0, step=1_000_000.0, format="%.2f")
    with col2:
        duration_months = st.number_input("⏳ مدت قرارداد (ماه):", min_value=1, step=1, value=12)

    contract_date_str = st.text_input("📅 تاریخ انعقاد قرارداد (شمسی):", placeholder="مثال: 1403/05/12")

    submitted = st.form_submit_button("✅ ثبت قرارداد", type="primary")

    if submitted:
        if not tracking_code.strip() or not title.strip():
            st.error("لطفاً کد رهگیری و عنوان قرارداد را تکمیل کنید.")
        else:
            # ─── Parse + convert Jalali date to Gregorian (ISO) ───
            try:
                jalali_date = jdatetime.date.fromstring(contract_date_str.strip().replace("-", "/"))
            except ValueError:
                st.error("فرمت تاریخ نامعتبر است. لطفاً تاریخ را به صورت YYYY/MM/DD وارد کنید.")
                st.stop()
            contract_date_iso = jalali_date.togregorian().isoformat()

            payload = {
                "tracking_code": tracking_code.strip(),
                "employer_classification_code": employer_choice,
                "university_national_id": university_choice,
                "researcher_national_id": researcher_choice,
                "title": title.strip(),
                "total_amount": float(total_amount),
                "contract_date": contract_date_iso,
                "duration_months": int(duration_months),
            }
            try:
                response = requests.post(f"{API_URL}/contracts/", json=payload, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    st.success(
                        f"🎉 قرارداد با موفقیت ثبت شد.\n"
                        f"کد: {data.get('contract_tracking_code')} | "
                        f"کارفرما: {data.get('employer_name')} | "
                        f"دانشگاه: {data.get('university_name')} | "
                        f"فناور: {data.get('researcher_name')}"
                    )
                    st.toast("✅ قرارداد جدید ثبت شد.", icon="📄")
                else:
                    detail = "خطای ناشناخته."
                    try:
                        detail = response.json().get("detail", detail)
                    except ValueError:
                        pass
                    st.error(f"❌ خطا در ثبت قرارداد: {detail}")
            except requests.exceptions.ConnectionError:
                st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
            except requests.exceptions.Timeout:
                st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except Exception as e:
                st.error(f"خطا در ارسال اطلاعات به سرور: {e}")
