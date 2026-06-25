# راهنمای سریع اجرای داشبورد

## نصب وابستگی‌ها

اگر هنوز Streamlit را نصب نکرده‌اید:

```bash
pip install -r requirements.txt
```

## اجرای داشبورد

از دایرکتوری اصلی پروژه دستور زیر را اجرا کنید:

```bash
streamlit run dashboard/app.py
```

یا می‌توانید مستقیماً از پوشه dashboard اجرا کنید:

```bash
cd dashboard
streamlit run app.py
```

## دسترسی به داشبورد

پس از اجرا، داشبورد به صورت خودکار در مرورگر پیش‌فرض باز می‌شود:
- آدرس محلی: http://localhost:8501
- آدرس شبکه: http://YOUR_IP:8501

## توقف داشبورد

برای توقف سرور Streamlit، در ترمینال `Ctrl+C` را فشار دهید.

## عیب‌یابی

### خطای اتصال به دیتابیس
اطمینان حاصل کنید که:
1. فایل `.env` در دایرکتوری اصلی پروژه موجود است
2. متغیر `DATABASE_URL` به درستی تنظیم شده است
3. سرویس PostgreSQL در حال اجرا است

### خطای ماژول پیدا نشد
از دایرکتوری اصلی پروژه (همان جایی که `core/` و `models/` هستند) دستور را اجرا کنید.

### پورت در حال استفاده
اگر پورت 8501 در حال استفاده است:
```bash
streamlit run dashboard/app.py --server.port 8502
```

## گزینه‌های پیشرفته

### تغییر تم
```bash
streamlit run dashboard/app.py --theme.base "dark"
```

### اجرا بدون باز شدن مرورگر
```bash
streamlit run dashboard/app.py --server.headless true
```

### مشاهده لاگ‌ها
Streamlit به صورت خودکار لاگ‌ها را در ترمینال نمایش می‌دهد.
