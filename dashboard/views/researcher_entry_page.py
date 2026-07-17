# File: views/researcher_entry_page.py
"""Phase 4 - New Researcher (فناور) registration form."""
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/v1"

# ─── Aggressive RTL override + compact Persian theme ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
* { font-family: 'Vazirmatn', sans-serif !important; }
.block-container, .stTextInput, .stNumberInput, .stSelectbox, .stCheckbox, p, div {
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
</style>
""", unsafe_allow_html=True)

st.title("🧑‍🔬 فرم ثبت اطلاعات فناور")


def _fetch_universities():
    """Fetch universities for the dropdown; returns list or [] with friendly error."""
    try:
        resp = requests.get(f"{API_URL}/universities/lookup", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"خطا در دریافت لیست موسسات: {resp.status_code}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
        return []
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
        return []
    except Exception as e:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت موسسات: {e}")
        return []


fetched_universities = _fetch_universities()
# Smart mapping: display names in the UI, resolve to national_id on submit.
university_map = {u["name"]: u["national_id"] for u in fetched_universities}

ACADEMIC_RANKS = ["استاد", "دانشیار", "استادیار", "مربی", "پژوهشگر", "سایر"]
EDUCATION_LEVELS = ["دکتری", "کارشناسی ارشد", "کارشناسی", "سایر"]
RESEARCHER_TYPES = ["هیات علمی", "پژوهشگر آزاد", "دانشجو", "سایر"]
STATUS_OPTIONS = {"فعال": "Active", "غیرفعال": "Inactive"}

with st.form("researcher_entry_form", clear_on_submit=False):
    st.subheader("۱. اطلاعات هویتی")

    national_code = st.text_input("🪪 کد ملی فناور:", placeholder="۱۰ رقم", max_chars=10)

    col_first, col_last = st.columns(2)
    with col_first:
        first_name = st.text_input("👤 نام:")
    with col_last:
        last_name = st.text_input("👥 نام خانوادگی:")

    col_mobile, col_email = st.columns(2)
    with col_mobile:
        mobile = st.text_input("📱 تلفن همراه (اختیاری):", placeholder="مثال: 09123456789")
    with col_email:
        email = st.text_input("✉️ ایمیل (اختیاری):", placeholder="example@mail.com")

    st.markdown("---")
    st.subheader("۲. اطلاعات علمی و وابستگی سازمانی")

    if university_map:
        university_name = st.selectbox("🏫 موسسه محل فعالیت:", options=list(university_map.keys()))
    else:
        st.warning("هیچ موسسه‌ای برای انتخاب یافت نشد. ابتدا یک موسسه ثبت کنید.")
        university_name = None

    col_rank, col_edu = st.columns(2)
    with col_rank:
        academic_rank = st.selectbox("🎓 مرتبه علمی:", options=ACADEMIC_RANKS)
    with col_edu:
        education_level = st.selectbox("🎓 سطح تحصیلات:", options=EDUCATION_LEVELS)

    researcher_type = st.selectbox("🏷️ نوع فناور:", options=RESEARCHER_TYPES)
    status_label = st.selectbox("🟢 وضعیت:", options=list(STATUS_OPTIONS.keys()), index=0)

    submitted = st.form_submit_button("✅ ثبت فناور", type="primary")

    if submitted:
        if university_name is None:
            st.error("موسسه محل فعالیت قابل انتخاب نیست.")
        elif not national_code.strip() or len(national_code.strip()) != 10 or not national_code.strip().isdigit():
            st.error("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        elif not first_name.strip() or not last_name.strip():
            st.error("لطفاً نام و نام خانوادگی را وارد کنید.")
        else:
            payload = {
                "national_code": national_code.strip(),
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "mobile": mobile.strip() or None,
                "email": email.strip() or None,
                "academic_rank": academic_rank,
                "education_level": education_level,
                "researcher_type": researcher_type,
                "university_id": university_map[university_name],
                "status": STATUS_OPTIONS[status_label],
            }
            try:
                response = requests.post(f"{API_URL}/researchers/", json=payload, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    st.success(
                        f"🎉 فناور با موفقیت ثبت شد.\n"
                        f"کد ملی: {data.get('national_code')} | "
                        f"نام: {data.get('full_name')} | "
                        f"مرتبه علمی: {data.get('academic_rank')} | "
                        f"موسسه: {data.get('university_id')}"
                    )
                    st.toast("✅ فناور جدید ثبت شد.", icon="🧑‍🔬")
                else:
                    detail = "خطای ناشناخته."
                    try:
                        detail = response.json().get("detail", detail)
                    except ValueError:
                        pass
                    st.error(f"❌ خطا در ثبت فناور: {detail}")
            except requests.exceptions.ConnectionError:
                st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
            except requests.exceptions.Timeout:
                st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except Exception as e:
                st.error(f"خطا در ارسال اطلاعات به سرور: {e}")
