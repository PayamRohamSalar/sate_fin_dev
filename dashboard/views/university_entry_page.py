# File: views/university_entry_page.py
"""Phase 4 - New University / Executing Institution registration form."""
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

st.title("🏫 فرم ثبت موسسه مجری جدید")

IRAN_PROVINCES = [
    "تهران", "اصفهان", "فارس", "خراسان رضوی", "آذربایجان شرقی", "مازندران", "گیلان",
    "کرمان", "یزد", "البرز", "قم", "سمنان", "هرمزگان", "بوشهر", "سیستان و بلوچستان",
    "لرستان", "همدان", "کردستان", "کرمانشاه", "ایلام", "خوزستان", "چهارمحال و بختیاری",
    "کهگیلویه و بویراحمد", "گلستان", "آذربایجان غربی", "اردبیل", "زنجان", "قزوین",
    "مرکزی", "خراسان شمالی", "خراسان جنوبی", "سایر",
]

UNIVERSITY_TYPES = [
    "دانشگاه دولتی",
    "دانشگاه آزاد",
    "دانشگاه غیرانتفاعی",
    "پژوهشگاه",
    "پارک علم و فناوری",
    "شرکت دانش بنیان",
    "موسسه آموزش عالی",
]

with st.form("university_entry_form", clear_on_submit=False):
    st.subheader("۱. اطلاعات موسسه")

    national_id = st.text_input("🪪 شناسه ملی موسسه:", placeholder="مثال: 14001234567")
    name = st.text_input("🏛️ نام کامل موسسه/دانشگاه:")

    col1, col2 = st.columns(2)
    with col1:
        province = st.selectbox("🗺️ استان محل استقرار:", options=IRAN_PROVINCES)
    with col2:
        university_type = st.selectbox("🏷️ نوع موسسه:", options=UNIVERSITY_TYPES)

    is_active = st.checkbox("✅ وضعیت فعالیت: فعال / غیرفعال", value=True,
                            help="تیک خورده = فعال، بدون تیک = غیرفعال")

    submitted = st.form_submit_button("✅ ثبت موسسه", type="primary")

    if submitted:
        if not national_id.strip() or not name.strip():
            st.error("لطفاً شناسه ملی و نام موسسه را تکمیل کنید.")
        else:
            payload = {
                "national_id": national_id.strip(),
                "name": name.strip(),
                "province": province,
                "university_type": university_type,
                "is_active": is_active,
            }
            try:
                response = requests.post(f"{API_URL}/universities/", json=payload, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    st.success(
                        f"🎉 موسسه با موفقیت ثبت شد.\n"
                        f"شناسه ملی: {data.get('national_id')} | "
                        f"نام: {data.get('name')} | "
                        f"نوع: {data.get('university_type')} | "
                        f"استان: {data.get('province')} | "
                        f"وضعیت: {data.get('status')}"
                    )
                    st.toast("✅ موسسه جدید ثبت شد.", icon="🏫")
                else:
                    detail = "خطای ناشناخته."
                    try:
                        detail = response.json().get("detail", detail)
                    except ValueError:
                        pass
                    st.error(f"❌ خطا در ثبت موسسه: {detail}")
            except requests.exceptions.ConnectionError:
                st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
            except requests.exceptions.Timeout:
                st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except Exception as e:
                st.error(f"خطا در ارسال اطلاعات به سرور: {e}")
