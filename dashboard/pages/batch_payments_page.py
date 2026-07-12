# File: pages/batch_payments_page.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Backend API Base URL
API_URL = "http://localhost:8000/api/v1"

st.set_page_config(layout="wide")
st.title("📂 فرم ثبت دسته‌ای لیست پرداخت (کارتابل صندوق عتف)")

# 1. Initialize Temporary Cart in Session State
if "payment_cart" not in st.session_state:
    st.session_state.payment_cart = []

# 2. Top Bar: Global Batch Configuration
st.subheader("۱. اطلاعات کلی لیست پرداخت")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    series_number = st.number_input("شماره سری پرداخت (لیست):", min_value=1, value=15, step=1)
with col_s2:
    # Default to current Jalali year (1405 based on conceptual doc context)
    payment_year = st.number_input("سال پرداخت (شمسی):", min_value=1398, max_value=1410, value=1405)
with col_s3:
    st.info("💡 این اطلاعات به طور خودکار به تمام ردیف‌های این لیست اعمال خواهد شد.")

st.markdown("---")

# 3. Data Entry Section (Row by Row)
st.subheader("۲. ورود اطلاعات ردیف جدید")

# Live search for contracts
search_query = st.text_input("🔍 جستجوی قرارداد (کد رهگیری یا بخشی از عنوان قرارداد):")
selected_contract = None

if search_query:
    try:
        response = requests.get(f"{API_URL}/contracts/search", params={"q": search_query})
        if response.status_code == 200 and response.json():
            contracts_found = response.json()
            # Format display for the selectbox
            options = {f"{c['contract_tracking_code']} - {c['title'][:40]}...": c for c in contracts_found}
            choice = st.selectbox("قرارداد مورد نظر را انتخاب کنید:", list(options.keys()))
            selected_contract = options[choice]
            
            # Auto-fill Read-only data to assure the clerk
            st.success(f"🏢 متقاضی (شرکت مادر): {selected_contract['employer_name']} | 🎓 مجری: {selected_contract['university_name']} | 🧑‍💻 فناور: {selected_contract['researcher_name']}")
        else:
            st.warning("هیچ قراردادی با این مشخصات یافت نشد.")
    except Exception as e:
        st.error(f"خطا در اتصال به بک‌اند: {e}")

# Other input fields for the row
col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    pay_tracking_code = st.text_input("کد رهگیری پرداخت (از سامانه ساتع):")
with col_r2:
    amount = st.number_input("مبلغ پرداختی (ریال):", min_value=0.0, step=1000000.0, format="%.2f")
with col_r3:
    funding_year = st.number_input("پرداخت از محل سال مالی (شمسی):", min_value=1398, max_value=1410, value=1402)

# Row Validation and Insertion into Temporary Cart
if st.button("➕ بررسی و اضافه کردن به لیست"):
    if not selected_contract or not pay_tracking_code or amount <= 0:
        st.error("لطفاً تمامی فیلدهای الزامی ردیف را تکمیل کنید.")
    else:
        # Calculate pending amount for this employer in the current cart
        employer_code = selected_contract['employer_classification_code']
        pending_amount = sum(item['amount'] for item in st.session_state.payment_cart 
                             if item['employer_code'] == employer_code and item['funding_year'] == funding_year)
        
        # Call Backend to validate draft with pending cart consideration
        val_payload = {
            "contract_tracking_code": selected_contract['contract_tracking_code'],
            "amount": amount,
            "funding_year": funding_year,
            "pending_cart_amount": pending_amount
        }
        
        try:
            val_response = requests.post(f"{API_URL}/payments/validate-draft", json=val_payload)
            if val_response.status_code == 200:
                # Add to local state (Memory Cart)
                new_row = {
                    "tracking_code": pay_tracking_code,
                    "contract_tracking_code": selected_contract['contract_tracking_code'],
                    "title": selected_contract['title'],
                    "employer_name": selected_contract['employer_name'],
                    "employer_code": employer_code,
                    "amount": amount,
                    "funding_year": funding_year,
                    "payment_year": payment_year,
                    "series": str(series_number)
                }
                st.session_state.payment_cart.append(new_row)
                st.toast("✅ ردیف با موفقیت تایید و به لیست پیش‌نویس اضافه شد.", icon="🔥")
            else:
                err_detail = val_response.json().get('detail', 'موجودی کافی نیست.')
                st.error(f"❌ خطای عدم کفایت موجودی: {err_detail}")
        except Exception as e:
            st.error(f"خطا در ارتباط با سرور اعتبارسنجی: {e}")

st.markdown("---")

# 4. Display Current Temporary Cart Table
st.subheader("۳. لیست پیش‌نویس پرداخت‌های در حال انتظار (ثبت موقت)")
if st.session_state.payment_cart:
    df_cart = pd.DataFrame(st.session_state.payment_cart)
    # Re-order columns for display
    display_df = df_cart[['series', 'tracking_code', 'contract_tracking_code', 'employer_name', 'amount', 'funding_year', 'payment_year']]
    display_df.columns = ['سری', 'کد رهگیری پرداخت', 'کد قرارداد', 'نام کارفرما', 'مبلغ (ریال)', 'محل سال مالی', 'سال خروج پول']
    st.dataframe(display_df, use_container_width=True)
    
    if st.button("🗑️ خالی کردن کل لیست"):
        st.session_state.payment_cart = []
        st.rerun()
        
    st.markdown("### 🚀 نهایی‌سازی و ثبت در دیتابیس")
    if st.button("💾 تأیید نهایی و ارسال لیست به صندوق", type="primary"):
        # Format payload for bulk submit
        bulk_payload = {
            "payments": [
                {
                    "tracking_code": item['tracking_code'],
                    "contract_tracking_code": item['contract_tracking_code'],
                    "amount": item['amount'],
                    "series": item['series'],
                    "payment_year": item['payment_year'],
                    "funding_year": item['funding_year']
                } for item in st.session_state.payment_cart
            ]
        }
        
        try:
            submit_res = requests.post(f"{API_URL}/payments/bulk-submit", json=bulk_payload)
            if submit_res.status_code == 201:
                submitted_count = submit_res.json().get("submitted_count", 0)
                st.success(f"🎉 لیست با موفقیت نهایی شد! {submitted_count} قلم پرداخت ثبت و قفل گردید.")
                st.session_state.payment_cart = [] # Clear cart on success
            else:
                st.error(f"❌ خطا در ثبت نهایی: {submit_res.json().get('detail')}")
        except Exception as e:
            st.error(f"خطا در ارسال نهایی به سرور: {e}")
else:
    st.info("لیست پیش‌نویس در حال حاضر خالی است. ردیف‌های پرداخت را از بخش بالا اضافه کنید.")