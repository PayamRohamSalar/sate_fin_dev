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


universities = _fetch_universities()

ACADEMIC_RANKS = ["استاد", "دانشیار", "استادیار", "مربی", "پژوهشگر", "سایر"]

with st.form("researcher_entry_form", clear_on_submit=False):
    st.subheader("۱. اطلاعات فناور")

    national_id = st.text_input("🪪 کد ملی فناور:", placeholder="۱۰ رقم", max_chars=10)
    full_name = st.text_input("👤 نام و نام خانوادگی:")

    if universities:
        uni_options = {item["national_id"]: f"{item['name']} ({item['national_id']})" for item in universities}
        university_national_id = st.selectbox(
            "🏫 موسسه محل فعالیت:",
            options=list(uni_options.keys()),
            format_func=lambda nid: uni_options[nid],
        )
    else:
        st.warning("هیچ موسسه‌ای برای انتخاب یافت نشد. ابتدا یک موسسه ثبت کنید.")
        university_national_id = None

    academic_rank = st.selectbox("🎓 مرتبه علمی:", options=ACADEMIC_RANKS)

    submitted = st.form_submit_button("✅ ثبت فناور", type="primary")

    if submitted:
        if university_national_id is None:
            st.error("موسسه محل فعالیت قابل انتخاب نیست.")
        elif not national_id.strip() or len(national_id.strip()) != 10 or not national_id.strip().isdigit():
            st.error("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        elif not full_name.strip():
            st.error("لطفاً نام و نام خانوادگی را وارد کنید.")
        else:
            payload = {
                "national_id": national_id.strip(),
                "full_name": full_name.strip(),
                "university_national_id": university_national_id,
                "academic_rank": academic_rank,
            }
            try:
                response = requests.post(f"{API_URL}/researchers/", json=payload, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    st.success(
                        f"🎉 فناور با موفقیت ثبت شد.\n"
                        f"کد ملی: {data.get('national_id')} | "
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
