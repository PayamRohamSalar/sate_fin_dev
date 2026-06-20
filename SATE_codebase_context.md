# Directory Structure
./
    create_project_structure.py
    generate_context.py
    main.py
    SATE_codebase_context.md
    test_engine_cli.py
    .pgdata/
        base/
            1/
            16384/
            4/
            5/
        global/
        pg_commit_ts/
        pg_dynshmem/
        pg_logical/
            mappings/
            snapshots/
        pg_multixact/
            members/
            offsets/
        pg_notify/
        pg_replslot/
        pg_serial/
        pg_snapshots/
        pg_stat/
        pg_stat_tmp/
        pg_subtrans/
        pg_tblspc/
        pg_twophase/
        pg_wal/
            archive_status/
            summaries/
        pg_xact/
    api/
        __init__.py
        v1/
            api_router.py
            __init__.py
            endpoints/
                employers.py
                __init__.py
    core/
        database.py
    data/
        Archive/
            Payments/
    Docs/
        Phase1_Complete.md
        Phase2_Start.md
    models/
        contract.py
        deposits.py
        employer.py
        payment.py
        researchers.py
        university.py
    results/
    schemas/
        employer_schema.py
        __init__.py
    scripts/
        append_new_mandates.py
        check_excel.py
        example_1.py
        generate_financial_report.py
        import_contracts.py
        import_deposits.py
        import_employers.py
        import_payments.py
        import_researchers.py
        import_universities.py
        process_budgets.py
        verify_universities.py
    services/
        financial_engine.py


# File Contents
==================================================

## File: create_project_structure.py
------------------------------
from pathlib import Path

# مسیر اصلی پروژه
project_path = Path(r"D:\OneDrive\AI-Project\SATE_Fin_Dev")

# پوشه‌هایی که باید ساخته شوند
folders = [
    "core",
    "models",
    "data",
    "scripts",
]

# ساخت مسیر اصلی پروژه در صورت نبودن
project_path.mkdir(parents=True, exist_ok=True)

# ساخت پوشه‌ها
for folder in folders:
    folder_path = project_path / folder
    folder_path.mkdir(exist_ok=True)

# ساخت فایل .env در صورت نبودن
env_file = project_path / ".env"

if not env_file.exists():
    env_file.write_text(
        """# Environment Variables
# Database Configuration

DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
""",
        encoding="utf-8"
    )

print("ساختار پروژه با موفقیت ایجاد شد:")
print(project_path)


## File: generate_context.py
------------------------------
import os

def generate_codebase_summary(root_dir, output_file):
    """
    Traverses the project directory, creates a tree structure,
    and appends the content of relevant files.
    """
    # Exclude directories that do not contain source code
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode'}
    
    # Target specific file types relevant to SATE Financial System MVP
    allowed_extensions = {'.py', '.sql', '.md', '.json', '.env.example'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 1. Document the Directory Structure
        outfile.write("# Directory Structure\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if any(f.endswith(ext) for ext in allowed_extensions):
                    outfile.write(f"{sub_indent}{f}\n")

        outfile.write("\n\n# File Contents\n")
        outfile.write("="*50 + "\n\n")

        # 2. Append the Content of Each Target File
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if any(f.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, f)
                    relative_path = os.path.relpath(file_path, root_dir)
                    
                    outfile.write(f"## File: {relative_path}\n")
                    outfile.write("-" * 30 + "\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read() + "\n\n")
                    except Exception as e:
                        outfile.write(f"[Error reading file: {e}]\n\n")

if __name__ == "__main__":
    # Run in the current SATE_Fin_Dev directory
    project_path = "." 
    output_filename = "SATE_codebase_context.md"
    generate_codebase_summary(project_path, output_filename)
    print(f"Success! Please upload '{output_filename}' to the chat.")

## File: main.py
------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.api_router import api_router

app = FastAPI(
    title="SATE Financial System API",
    description="Backend REST API for SATE Financial Dashboard (MVP)",
    version="1.0.0"
)

# CORS configuration for Frontend (Streamlit/React) integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
def health_check():
    """
    Root endpoint to verify the API is running.
    """
    return {
        "status": "Operational", 
        "message": "Welcome to SATE Financial System API",
        "phase": 2
    }


## File: SATE_codebase_context.md
------------------------------


## File: test_engine_cli.py
------------------------------
#!/usr/bin/env python3
"""
CLI Test Script for Financial Engine
=====================================
This script directly tests the calculate_real_balance function from the financial engine
by fetching a real employer from the database and calculating their balance.
"""

from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.financial_engine import calculate_real_balance
from models.employer import Employer


def test_financial_engine():
    """
    Test the financial engine by calculating balance for a real employer from the database.
    """
    print("=" * 70)
    print("SATE Financial Engine - CLI Test")
    print("=" * 70)
    
    # Initialize database session
    db: Session = SessionLocal()
    
    try:
        # Fetch one employer from the database dynamically
        employer = db.query(Employer).filter(
            Employer.is_deleted == False
        ).first()
        
        if not employer:
            print("\n❌ No employers found in the database.")
            print("Please ensure the database is populated with employer data.")
            return
        
        print(f"\n✓ Found Employer: {employer.employer_name}")
        print(f"  Classification Code: {employer.classification_code}")
        print(f"  Parent Code: {employer.parent_code or 'N/A (Top-level employer)'}")
        
        # Test for multiple funding years
        test_years = [1402, 1403, 1404]
        
        print(f"\n{'Year':<10} {'Balance (Rials)':<20} {'Status':<15}")
        print("-" * 70)
        
        for year in test_years:
            try:
                balance = calculate_real_balance(
                    db=db,
                    employer_code=employer.classification_code,
                    funding_year=year
                )
                
                # Format the balance with thousand separators
                balance_formatted = f"{balance:,.2f}"
                status = "✓ Success"
                
                print(f"{year:<10} {balance_formatted:<20} {status:<15}")
                
            except Exception as e:
                print(f"{year:<10} {'Error':<20} ❌ {str(e)}")
        
        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        print("\n✓ Database connection closed.")


if __name__ == "__main__":
    test_financial_engine()


## File: api\__init__.py
------------------------------


## File: api\v1\api_router.py
------------------------------
from fastapi import APIRouter

from api.v1.endpoints import employers

# Create the main API router for version 1
api_router = APIRouter()

# Include sub-routers for different endpoint groups
api_router.include_router(employers.router)

# Future routers can be added here as the system grows:
# api_router.include_router(contracts.router)
# api_router.include_router(payments.router)
# api_router.include_router(deposits.router)


## File: api\v1\__init__.py
------------------------------


## File: api\v1\endpoints\employers.py
------------------------------
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from core.database import get_db
from services.financial_engine import calculate_real_balance
from schemas.employer_schema import BalanceResponse
from models.employer import Employer

router = APIRouter(
    prefix="/employers",
    tags=["Employers"]
)


@router.get("/{employer_id}/balance", response_model=BalanceResponse)
def get_employer_balance(
    employer_id: str = Path(..., description="Employer classification code"),
    funding_year: int = Query(..., description="Funding year (fiscal year) for balance calculation", ge=1300, le=1500),
    db: Session = Depends(get_db)
):
    """
    Calculate and return the real financial balance for a specific employer and funding year.
    
    The balance is calculated as:
    - Total deposits (including subsidiaries) - Total payments linked to employer's contracts
    
    **Parameters:**
    - `employer_id`: The employer's classification code
    - `funding_year`: The fiscal year for the balance calculation (Persian calendar year)
    
    **Returns:**
    - Employer code
    - Funding year
    - Total calculated balance
    - Current inquiry date in Jalali format
    """
    
    # Verify that the employer exists in the database
    employer = db.query(Employer).filter(
        Employer.classification_code == employer_id,
        Employer.is_deleted == False
    ).first()
    
    if not employer:
        raise HTTPException(
            status_code=404,
            detail=f"Employer with code '{employer_id}' not found or has been deleted."
        )
    
    # Calculate the real balance using the financial engine
    try:
        balance = calculate_real_balance(db, employer_id, funding_year)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating balance: {str(e)}"
        )
    
    # Return the response with current Jalali date
    return BalanceResponse(
        employer_code=employer_id,
        funding_year=funding_year,
        total_balance=balance,
        inquiry_date_jalali=BalanceResponse.get_current_jalali_date()
    )


## File: api\v1\endpoints\__init__.py
------------------------------


## File: core\database.py
------------------------------
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please configure it in .env.")

# Create engine with connection pooling settings
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to yield database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


## File: Docs\Phase1_Complete.md
------------------------------
# سند جامع فاز اول توسعه سامانه مالی ساتع (SATE\_Fin\_Dev)

موضوع: معماری پایگاه داده، زیرساخت داده‌ها (ETL) و استقرار منطق پایه مالی  
نسخه: v0.2.0-core-db-completed

## ۱. مقدمه و کلیات پروژه

پروژه SATE\_Fin\_Dev یک سامانه مدیریت مالی و حسابداری تعهدی است که با هدف رصد، تجمیع و محاسبه دقیق اعتبارات تکلیفی، واریزی‌ها، قراردادهای پژوهشی و پرداختی‌های مرتبط با مشمولین قانون بودجه توسعه می‌یابد.  
در فاز اول (MVP)، تمرکز بر روی انتقال داده‌های خام (فایل‌های Excel Wide-Format و CSV)، پاک‌سازی آن‌ها، و استقرار یک پایگاه داده رابطه‌ای (Relational) یکپارچه و بهینه بوده است.

## ۲. زیرساخت و محیط توسعه (Environment Setup)

* محیط مجازی: ایزوله‌شده با استفاده از Conda (sate\_env).  
* پایگاه داده: PostgreSQL (دیتابیس sate\_db).  
* ابزارهای توسعه (Stack): پایتون (Python)، موتور ORM دیتابیس (SQLAlchemy)، ابزار پردازش داده‌ها (Pandas) و کتابخانه تبدیل تاریخ (jdatetime).  
* مدیریت نسخه: اتصال موفق به GitHub با رعایت اصول امنیتی (.gitignore برای فایل‌های حساس .env و data).

## ۳. معماری پایگاه داده و جداول (Database Schema & Relationships)

تمامی جداول به ویژگی SoftDeleteMixin (حذف منطقی) مجهز شده‌اند تا از حذف فیزیکی و غیرقابل بازگشت داده‌های مالی جلوگیری شود. روابط کلید خارجی (Foreign Keys) با دقت پیاده‌سازی شده‌اند:

1. جدول مشمولین (employers): *جدول Master (پدر)*  
   * کلید اصلی: classification\_code (شماره طبقه‌بندی).  
   * فیلدهای کلیدی: نام مشمول، نوع مشمول (Mother/Subsidiary/Independent)، استان، و ستون افزوده شده affairs\_category (عنوان امور \- برای گزارش‌گیری‌های کلان).  
2. مدیریت بودجه و اعتبارات (deposits): تبدیل ساختار Wide به Long با معماری Master-Detail:  
   * جدول اعتبارات تکلیفی (annual\_mandates): متصل به employers. نگهداری اعتبار ابلاغی در هر fiscal\_year.  
   * جدول فیش‌های واریزی (deposit\_receipts): متصل به employers. ثبت جزئیات دقیق مبالغ واریز شده به حساب صندوق در هر سال.  
3. جدول دانشگاه‌ها/موسسات اجرایی (universities): *جدول پایه*  
   * کلید اصلی: national\_id (شناسه ملی موسسه).  
   * فیلدهای کلیدی: نام موسسه، استان، نوع موسسه و وضعیت.  
4. جدول فناوران/مجریان (researchers): *فرزند دانشگاه‌ها*  
   * کلید اصلی: national\_code (کد ملی).  
   * کلید خارجی: university\_id (متصل به جدول دانشگاه‌ها).  
   * فیلدهای کلیدی: نام، ایمیل، موبایل، درجه علمی و وضعیت.  
5. جدول قراردادها (contracts): *قلب تپنده و نقطه اتصال (Junction Table)*  
   * کلید اصلی: tracking\_code (کد رهگیری).  
   * کلیدهای خارجی (۳ اتصال همزمان): \- employer\_code (کارفرما)  
     * university\_id (دانشگاه مجری)  
     * researcher\_id (فناور/استاد)  
   * فیلدهای کلیدی: شماره قرارداد، مبلغ کل، تاریخ قرارداد (میلادی)، proposal\_id (برای توسعه‌های آینده).  
6. جدول پرداختی‌ها (payments): *ثبت تراکنش‌ها*  
   * کلید اصلی: tracking\_code (کد رهگیری پرداخت).  
   * کلید خارجی: contract\_tracking\_code (متصل به قراردادها).  
   * فیلدهای کلیدی: سری پرداخت، مبلغ پرداختی، شماره و تاریخ ابلاغ نامه، attachment\_path (مسیر پیوست‌ها).

## ۴. قواعد محاسباتی و منطق تجاری (Core Financial Logic)

در این فاز، چند تصمیم حساس برای تضمین یکپارچگی محاسبات (Data Integrity) اتخاذ شد که باید در داشبوردها و توسعه API مد نظر قرار گیرند:

* تطبیق مقیاس پولی (Base Unit): تمامی ارقام مالی که در اکسل بر حسب «میلیارد ریال» بودند، در مرحله ETL در $10^9$ ضرب شدند. دیتابیس تمامی مبالغ را به عنوان «ریال پایه» با تایپ Numeric(22, 0\) ذخیره می‌کند تا از خطای اعشار و سرریز جلوگیری شود.  
* استانداردسازی تاریخ‌ها: پایگاه داده فقط تاریخ‌های میلادی (Gregorian) را می‌شناسد. تاریخ‌های شمسی در زمان Import توسط jdatetime به میلادی تبدیل شده‌اند. (در لایه فرانت‌اند/داشبورد باید مجدداً به شمسی رندر شوند).  
* سال مالی در برابر سال نقدینگی (Funding Year vs. Payment Year) \- \[بسیار حیاتی\]: در محاسبه مانده حساب مشمولین، سال پرداخت (payment\_year) بی‌اهمیت است. محاسبات دقیق مالی، تفریق پرداختی‌ها از اعتبارات بر اساس سالِ تأمین اعتبار (funding\_year) است. (مثال: پرداختی‌های سال ۱۴۰۴ که از محل اعتبار ۱۴۰۲ بوده‌اند، باید از مانده حساب سال ۱۴۰۲ کسر شوند).

## ۵. استراتژی‌های مهندسی داده (ETL Pipelines)

اسکریپت‌های انتقال داده (موجود در پوشه scripts/) با ویژگی‌های زیر توسعه یافتند:

* جلوگیری از مشکل N+1 Query: در اعتبارسنجی کلیدهای خارجی (نظیر چک کردن وجود دانشگاهِ یک فناور)، به جای کوئری‌های تک‌به‌تک، شناسه‌های مرجع در حافظه (یک Set در پایتون) بارگذاری شده و تطبیق با پیچیدگی O(1) انجام می‌شود.  
* پاک‌سازی داده‌ها (Data Cleaning): فیلتر کردن ردیف‌های دارای ارورهای اکسلی مثل \#REF\!، حذف کاما از ارقام ریالی، و تبدیل ایمن مقادیرِ خالی (NaN) به Null در دیتابیس.  
* اسکریپت اثبات مفهوم (PoC): اسکریپت generate\_financial\_report.py با استفاده از Pandas توسعه یافت که صحت منطق تجاری و کسر پرداختی‌ها از اعتبارات (بر اساس Funding Year) را تأیید کرده و خروجی موفق در results/ ایجاد نمود.

وضعیت فعلی برای شروع فاز ۲: لایه ذخیره‌سازی داده (Data Persistence Layer) صددرصد تکمیل و پایدار است. آماده ورود به توسعه موتور محاسبات تحلیلی (BI)، لایه رابط برنامه‌نویسی (API) و طراحی داشبوردهای مدیریتی می‌باشیم.



## File: Docs\Phase2_Start.md
------------------------------
# سند نقشه راه و معماری کلان (Roadmap & Blueprint)

پروژه: سامانه مدیریت مالی و حسابداری تعهدی ساتع (SATE\_Fin\_Dev)  
موقعیت فعلی: پایان فاز اول (تکمیل لایه پایگاه داده و ETL)  
هدف سند: ترسیم مسیر توسعه فازهای ۲ تا ۵ تا رسیدن به یک محصول نهایی (Production-Ready)

## فاز ۲: توسعه هسته محاسباتی و لایه API (Backend & Business Logic)

اکنون که داده‌ها با موفقیت در دیتابیس مستقر شده‌اند، باید بستری فراهم کنیم تا این داده‌ها به صورت زنده، پردازش شده و در اختیار لایه‌های نمایشی قرار گیرند.

* تکنولوژی پیشنهادی: فریم‌ورک FastAPI (به دلیل سرعت بالا، مستندسازی خودکار و سازگاری عالی با SQLAlchemy) و Pydantic برای اعتبارسنجی داده‌ها.  
* اقدامات کلیدی:  
  1. طراحی موتور محاسبات مالی (Financial Engine): تبدیل اسکریپت گزارش‌گیری فعلی به توابع (Functions) زنده. این توابع در لحظه میزان پرداختی‌ها را بر اساس funding\_year (سال تأمین اعتبار) از mandated\_amount (اعتبار تکلیفی) کسر می‌کنند.  
  2. توسعه Endpoint های RESTful: ساخت مسیرهایی برای دریافت اطلاعات (مثلاً GET /api/employers/{id}/balance برای دریافت مانده یک کارفرما).  
  3. مدیریت تاریخ‌های شمسی: تعبیه توابع jdatetime در لایه API تا تمام تاریخ‌های میلادیِ دیتابیس، در خروجی API به صورت شمسی و خوانا (YYYY/MM/DD) به کاربر نمایش داده شوند.

## فاز ۳: هوش تجاری و داشبوردهای مدیریتی (BI & Data Visualization)

هدف این فاز، تبدیل اعداد خام و JSONها به نمودارهای تعاملی و داشبوردهای مدیریتی برای تصمیم‌گیری است.

* تکنولوژی پیشنهادی: Streamlit (بهترین و سریع‌ترین گزینه برای داشبوردهای مبتنی بر داده در پایتون) یا ترکیب React/Vue.js در صورت نیاز به یک وب‌سایت کاملاً سفارشی.  
* اقدامات کلیدی:  
  1. داشبورد کلان (Executive Dashboard): نمایش مجموع اعتبارات تکلیفی کل کشور، مجموع واریزی‌ها به صندوق و مانده کل سیستم.  
  2. داشبورد مشمولین (Employer View): صفحه‌ای که با انتخاب نام یک شرکت/وزارتخانه، نمودار میله‌ای مقایسه اعتبارات ابلاغی با پرداختی‌های واقعی آن‌ها را به تفکیک سال مالی نشان دهد.  
  3. داشبورد قراردادها و مجریان: رهگیری اینکه کدام دانشگاه‌ها یا فناوران بیشترین حجم ریالی قراردادها را به خود اختصاص داده‌اند.

## فاز ۴: احراز هویت، امنیت و کنترل دسترسی (Security & IAM)

یک سامانه مالی بدون سطوح دسترسی معنایی ندارد. ما باید مشخص کنیم چه کسی مجاز به دیدن چه اطلاعاتی است.

* تکنولوژی پیشنهادی: توکن‌های JWT (JSON Web Tokens) و رمزنگاری Passwords (مثلاً bcrypt).  
* اقدامات کلیدی:  
  1. تعریف نقش‌های کاربری (Role-based Access): نظیر Admin (مدیر کل سیستم)، Employer (نماینده شرکت مشمول) و University (نماینده دانشگاه).  
  2. اعمال فیلترهای امنیتی: مثلاً شرکت توانیر (پس از لاگین) فقط بتواند قراردادها و پرداختی‌های مربوط به خودش را ببیند و به داده‌های شرکت گاز دسترسی نداشته باشد.

## فاز ۵: توسعه فیچرهای جدید و استقرار نهایی (Expansion & Deployment)

تکمیل زنجیره ارزش سامانه و قرار دادن آن بر روی سرور واقعی.

* اقدامات کلیدی (توسعه):  
  1. افزودن جدول پیشنهاده‌ها (Proposals): اتصال proposal\_id در جدول قراردادها به جدول جدید پیشنهاده‌ها.  
  2. مدیریت فایل‌ها و پیوست‌ها: فعال‌سازی قابلیت آپلود فایل (Upload) برای ستون attachment\_path در پرداختی‌ها (ذخیره تصاویر نامه‌ها یا فیش‌های واریزی در سرور).  
* اقدامات کلیدی (استقرار \- DevOps):  
  1. کانتینرسازی سیستم با Docker (برای اجرای بی‌دردسر روی هر سروری).  
  2. تنظیم وب‌سرور Nginx یا Gunicorn.  
  3. انتقال پروژه از محیط Local (کامپیوتر شما) به یک سرور ابری (Cloud Server) لینوکسی برای دسترسی کاربران نهایی.

### سخن پایانی معمار سیستم:

مسیر پیش رو از یک "پایگاه داده استاتیک" به یک "سامانه زنده و پویای مالی" است. استراتژی ما در فاز بعدی (در چت جدید)، شروع مقتدرانه فاز ۲ (طراحی API و توابع محاسبات مالی) خواهد بود.  
این سند، نقشه راه ماست. هر زمان که آماده بودید، این سند و سند قبلی را در یک چت جدید بارگذاری کنید و فرمان شروع لایه Backend را صادر کنید\!  


## File: models\contract.py
------------------------------
from sqlalchemy import Column, String, ForeignKey, Date, Numeric, Integer, Text
from core.database import Base
from models.employer import SoftDeleteMixin


class Contract(SoftDeleteMixin, Base):
    __tablename__ = 'contracts'

    tracking_code = Column(String(50), primary_key=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code'), nullable=False)
    university_id = Column(String(20), ForeignKey('universities.national_id'), nullable=False)
    researcher_id = Column(String(10), ForeignKey('researchers.national_code'), nullable=False)
    proposal_id = Column(String(50), nullable=True)  # Future FK
    contract_number = Column(String(100), nullable=True)
    contract_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(22, 0), nullable=False)  # Base Rials
    title = Column(Text, nullable=False)
    duration_months = Column(Integer, nullable=True)
    status = Column(String(50), default='Active')


## File: models\deposits.py
------------------------------
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from models.employer import SoftDeleteMixin


class AnnualMandate(SoftDeleteMixin, Base):
    """Master table tracking mandated budget amounts per employer per fiscal year."""
    __tablename__ = 'annual_mandates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(22, 0), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('employer_code', 'fiscal_year', name='uq_employer_year_mandate'),
    )

    def __repr__(self):
        return f"<AnnualMandate(employer={self.employer_code}, year={self.fiscal_year}, amount={self.mandated_amount})>"


class DepositReceipt(SoftDeleteMixin, Base):
    """Detail table tracking individual deposit receipts per employer per fiscal year."""
    __tablename__ = 'deposit_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    deposit_amount = Column(Numeric(22, 0), nullable=False)
    deposit_date = Column(Date, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DepositReceipt(employer={self.employer_code}, year={self.fiscal_year}, amount={self.deposit_amount})>"


## File: models\employer.py
------------------------------
from sqlalchemy import Column, String, Boolean, CheckConstraint
from core.database import Base

class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

class Employer(SoftDeleteMixin, Base):
    __tablename__ = 'employers'

    classification_code = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    employer_type = Column(String(20), nullable=False)
    parent_code = Column(String(20), nullable=True)
    province = Column(String(50), nullable=False)
    affairs_category = Column(String(100), nullable=True)
    upper_organization = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default='Active')

    __table_args__ = (
        CheckConstraint("employer_type IN ('Mother', 'Subsidiary', 'Independent')", name="check_employer_type"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="check_employer_status"),
    )

## File: models\payment.py
------------------------------
from sqlalchemy import Column, String, ForeignKey, Date, Numeric, Integer
from core.database import Base
from models.employer import SoftDeleteMixin


class Payment(SoftDeleteMixin, Base):
    __tablename__ = 'payments'

    tracking_code = Column(String(50), primary_key=True)
    contract_tracking_code = Column(String(50), ForeignKey('contracts.tracking_code'), nullable=False)
    series = Column(String(50), nullable=True)
    amount = Column(Numeric(22, 0), nullable=False)  # Base Rials
    notification_letter_number = Column(String(100), nullable=True)
    notification_date = Column(Date, nullable=True)
    payment_year = Column(Integer, nullable=False)  # Cash flow year
    funding_year = Column(Integer, nullable=False)  # Budget consumption year
    attachment_path = Column(String(255), nullable=True)


## File: models\researchers.py
------------------------------
from sqlalchemy import Column, ForeignKey, String

from core.database import Base
from models.employer import SoftDeleteMixin


class Researcher(SoftDeleteMixin, Base):
    __tablename__ = "researchers"

    national_code = Column(String(10), primary_key=True)
    tracking_code = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    mobile = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    academic_rank = Column(String(50), nullable=True)
    university_id = Column(String(20), ForeignKey("universities.national_id"), nullable=False)
    education_level = Column(String(50), nullable=True)
    researcher_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="Active")


## File: models\university.py
------------------------------
from sqlalchemy import Column, String, Text
from core.database import Base
from models.employer import SoftDeleteMixin


class University(SoftDeleteMixin, Base):
    """University/Executing Institution model"""
    __tablename__ = 'universities'
    
    national_id = Column(String(20), primary_key=True, comment='شناسه ملی موسسه')
    tracking_code = Column(String(50), nullable=True, comment='کد رهگیری')
    name = Column(String(200), nullable=False, comment='نام موسسه')
    city = Column(String(100), nullable=True, comment='شهر')
    address = Column(Text, nullable=True, comment='آدرس')
    province = Column(String(50), nullable=False, comment='استان موسسه')
    university_type = Column(String(100), nullable=False, comment='نوع موسسه')
    status = Column(String(20), nullable=False, default='Active', comment='وضعیت')
    
    def __repr__(self):
        return f"<University(national_id='{self.national_id}', name='{self.name}')>"


## File: schemas\employer_schema.py
------------------------------
from pydantic import BaseModel, Field
from datetime import datetime
import jdatetime


class BalanceResponse(BaseModel):
    """
    Response schema for employer balance inquiry.
    """
    employer_code: str = Field(..., description="The employer's classification code")
    funding_year: int = Field(..., description="The funding year (fiscal year) for the balance calculation")
    total_balance: float = Field(..., description="The calculated real balance (deposits - payments)")
    inquiry_date_jalali: str = Field(..., description="Current date in Persian/Jalali calendar format")

    class Config:
        json_schema_extra = {
            "example": {
                "employer_code": "EMP001",
                "funding_year": 1403,
                "total_balance": 125000000.50,
                "inquiry_date_jalali": "1403/03/30"
            }
        }

    @staticmethod
    def get_current_jalali_date() -> str:
        """
        Returns the current date in Jalali (Persian) calendar format.
        Format: YYYY/MM/DD
        """
        now = jdatetime.datetime.now()
        return now.strftime("%Y/%m/%d")


## File: schemas\__init__.py
------------------------------


## File: scripts\append_new_mandates.py
------------------------------
import os
import sys
from pathlib import Path

import pandas as pd

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "New_Mandates.xlsx"

# Unit conversion: Excel values are in Billion Rials, convert to base Rials
BILLION = 1_000_000_000

# Target fiscal year for the new mandates
TARGET_FISCAL_YEAR = 1406


def normalize_code(value):
    """Normalize employer code by removing .0 suffix from numeric strings."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        return value[:-2]
    return value


def append_new_mandates(file_path: Path = EXCEL_FILE_PATH, fiscal_year: int = TARGET_FISCAL_YEAR):
    """Append new mandate records to the annual_mandates table without dropping existing data."""
    
    print(f"=== Append New Mandates for Fiscal Year {fiscal_year} ===")
    print(f"Reading Excel file: {file_path}")
    
    # Read the Excel file
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"Loaded {len(df)} rows from Excel")
    print(f"Columns: {list(df.columns)}")
    
    # Validate required columns
    required_cols = ['شماره طبقه بندی', 'اعتبار تکلیفی']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Normalize and prepare data
    df['employer_code'] = df['شماره طبقه بندی'].apply(normalize_code)
    df['mandated_amount'] = pd.to_numeric(df['اعتبار تکلیفی'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    df['mandated_amount'] = df['mandated_amount'] * BILLION
    
    print(f"Converted amounts to base Rials (×{BILLION:,})")
    
    # Start database transaction
    db = SessionLocal()
    try:
        # Get valid employer codes from database
        valid_codes = {emp.classification_code for emp in db.query(Employer.classification_code).all()}
        print(f"Found {len(valid_codes)} valid employer codes in database")
        
        # Get existing mandates for this fiscal year
        existing_mandates = {
            (m.employer_code, m.fiscal_year) 
            for m in db.query(AnnualMandate.employer_code, AnnualMandate.fiscal_year)
                      .filter(AnnualMandate.fiscal_year == fiscal_year)
                      .all()
        }
        print(f"Found {len(existing_mandates)} existing mandates for fiscal year {fiscal_year}")
        
        # Process each row
        added = 0
        updated = 0
        skipped_missing_employer = 0
        skipped_duplicate = 0
        
        for idx, row in df.iterrows():
            employer_code = row['employer_code']
            mandated_amount = float(row['mandated_amount'])
            
            # Validation 1: Check if employer exists
            if employer_code not in valid_codes:
                print(f"WARNING: Row {idx} - employer_code '{employer_code}' not found in database. Skipping.")
                skipped_missing_employer += 1
                continue
            
            # Validation 2: Check for existing mandate
            if (employer_code, fiscal_year) in existing_mandates:
                # Update existing record instead of creating duplicate
                existing_mandate = db.query(AnnualMandate).filter_by(
                    employer_code=employer_code,
                    fiscal_year=fiscal_year
                ).first()
                
                if existing_mandate:
                    old_amount = existing_mandate.mandated_amount
                    existing_mandate.mandated_amount = mandated_amount
                    updated += 1
                    print(f"Updated: {employer_code} - Year {fiscal_year}: {old_amount:,.2f} → {mandated_amount:,.2f} Rials")
                continue
            
            # Insert new mandate
            new_mandate = AnnualMandate(
                employer_code=employer_code,
                fiscal_year=fiscal_year,
                mandated_amount=mandated_amount
            )
            db.add(new_mandate)
            added += 1
        
        # Commit transaction
        db.commit()
        
        print("\n=== Import Summary ===")
        print(f"✓ Successfully added {added} new Annual_Mandate records")
        print(f"✓ Successfully updated {updated} existing Annual_Mandate records")
        print(f"⚠ Skipped {skipped_missing_employer} rows due to missing employer codes")
        print(f"ℹ Skipped {skipped_duplicate} rows due to existing mandates (already handled via update)")
        print(f"\nNote: All monetary values converted from Billion Rials to base Rials (×{BILLION:,})")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Database transaction failed. Rolled back.")
        print(f"Error details: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    append_new_mandates()


## File: scripts\check_excel.py
------------------------------
import pandas as pd
import sys

df = pd.read_excel('data/University.xlsx')

# Write to file to avoid console encoding issues
output_path = 'data/excel_info.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"Total rows: {len(df)}\n")
    f.write(f"Total columns: {len(df.columns)}\n\n")
    f.write("Column names:\n")
    for i, col in enumerate(df.columns):
        f.write(f"  {i}: {col}\n")
    
    f.write("\n\nFirst 5 rows sample:\n")
    f.write(df.head(5).to_string())
    
    f.write("\n\nData types:\n")
    f.write(str(df.dtypes))

print(f"Information written to {output_path}")


## File: scripts\example_1.py
------------------------------
import sys
import os
import pandas as pd

# این دو خط، مسیر اصلی پروژه را به پایتون می‌شناسانند تا پوشه core را پیدا کند
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# حالا پایتون می‌تواند core.database را پیدا کند
from core.database import engine

def run_pandas_example():
    print("Connecting to database and fetching employers data...")
    
    # خواندن کل جدول مشمولین از دیتابیس
    df_employers = pd.read_sql_table('employers', con=engine)
    
    print(f"\nTotal employers loaded: {len(df_employers)}")
    
    # نمایش ۵ رکورد اول
    print("\nFirst 5 records:")
    print(df_employers.head())
    
    # یک مثال تحلیلی: تعداد مشمولین به تفکیک استان
    print("\nEmployers count by province:")
    province_counts = df_employers['province'].value_counts()
    print(province_counts)

if __name__ == "__main__":
    run_pandas_example()

## File: scripts\generate_financial_report.py
------------------------------
"""
Financial Report Generator
Calculates employer balances by comparing mandated budgets against actual payments.
"""

import pandas as pd
import os
from pathlib import Path
from sqlalchemy import create_engine

# Import database engine
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.database import engine


def main():
    print("=" * 60)
    print("Financial Report Generator - Employer Balance Analysis")
    print("=" * 60)
    
    # Step 1: Extract data from database
    print("\n[1/5] Extracting data from database...")
    
    try:
        # Read tables into DataFrames
        df_employers = pd.read_sql_table('employers', con=engine)
        print(f"   ✓ Loaded {len(df_employers)} employers")
        
        df_mandates = pd.read_sql_table('annual_mandates', con=engine)
        print(f"   ✓ Loaded {len(df_mandates)} annual mandates")
        
        df_contracts = pd.read_sql_table('contracts', con=engine)
        print(f"   ✓ Loaded {len(df_contracts)} contracts")
        
        df_payments = pd.read_sql_table('payments', con=engine)
        print(f"   ✓ Loaded {len(df_payments)} payments")
        
    except Exception as e:
        print(f"   ✗ Error reading tables: {e}")
        return
    
    # Step 2: Aggregate payments by employer and funding year
    print("\n[2/5] Aggregating payments by employer and funding year...")
    
    # Merge payments with contracts to get employer_code for each payment
    df_payments_with_employer = df_payments.merge(
        df_contracts[['tracking_code', 'employer_code']],
        left_on='contract_tracking_code',
        right_on='tracking_code',
        how='left'
    )
    
    # Group by employer and funding year, sum the amounts
    df_payment_aggregates = df_payments_with_employer.groupby(
        ['employer_code', 'funding_year']
    )['amount'].sum().reset_index()
    
    df_payment_aggregates.rename(columns={'amount': 'total_payments'}, inplace=True)
    print(f"   ✓ Aggregated payments for {len(df_payment_aggregates)} employer-year combinations")
    
    # Step 3: Calculate balance
    print("\n[3/5] Calculating financial balances...")
    
    # Merge mandates with payment aggregates
    df_balance = df_mandates.merge(
        df_payment_aggregates,
        left_on=['employer_code', 'fiscal_year'],
        right_on=['employer_code', 'funding_year'],
        how='outer'
    )
    
    # Fill NaN values with 0
    df_balance['mandated_amount'] = df_balance['mandated_amount'].fillna(0)
    df_balance['total_payments'] = df_balance['total_payments'].fillna(0)
    
    # Use fiscal_year as the primary year column (coalesce with funding_year if needed)
    df_balance['year'] = df_balance['fiscal_year'].fillna(df_balance['funding_year']).astype(int)
    
    # Calculate balance
    df_balance['balance'] = df_balance['mandated_amount'] - df_balance['total_payments']
    
    print(f"   ✓ Calculated balances for {len(df_balance)} records")
    
    # Step 4: Format output with employer names
    print("\n[4/5] Formatting final report with employer names...")
    
    # Merge with employers to get names
    df_final = df_balance.merge(
        df_employers[['classification_code', 'name']],
        left_on='employer_code',
        right_on='classification_code',
        how='left'
    )
    
    # Select and rename columns to Persian
    df_final = df_final[[
        'employer_code',
        'name',
        'year',
        'mandated_amount',
        'total_payments',
        'balance'
    ]]
    
    df_final.columns = [
        'کد مشمول',
        'نام مشمول',
        'سال مالی',
        'اعتبار تکلیفی (ریال)',
        'جمع پرداختی (ریال)',
        'مانده (ریال)'
    ]
    
    # Sort by employer code and year
    df_final = df_final.sort_values(['کد مشمول', 'سال مالی'])
    
    print(f"   ✓ Final report contains {len(df_final)} rows")
    
    # Step 5: Export to Excel
    print("\n[5/5] Exporting to Excel...")
    
    # Ensure results directory exists
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    output_path = results_dir / 'financial_report_summary.xlsx'
    
    try:
        df_final.to_excel(output_path, index=False, engine='openpyxl')
        print(f"   ✓ Exported to: {output_path}")
    except Exception as e:
        print(f"   ✗ Error exporting to Excel: {e}")
        return
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("REPORT SUMMARY")
    print("=" * 60)
    print(f"Total employers: {df_final['کد مشمول'].nunique()}")
    print(f"Total fiscal years: {df_final['سال مالی'].nunique()}")
    print(f"Total mandated amount: {df_final['اعتبار تکلیفی (ریال)'].sum():,.0f} Rials")
    print(f"Total payments: {df_final['جمع پرداختی (ریال)'].sum():,.0f} Rials")
    print(f"Total remaining balance: {df_final['مانده (ریال)'].sum():,.0f} Rials")
    print("=" * 60)
    print("\n✓ Financial report generation completed successfully!")


if __name__ == '__main__':
    main()


## File: scripts\import_contracts.py
------------------------------
import pandas as pd
import sys
from pathlib import Path
import io
import jdatetime
from decimal import Decimal

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from models.contract import Contract
from models.employer import Employer
from models.university import University
from models.researchers import Researcher


def parse_persian_date(date_str):
    """Parse Persian date string (e.g., '1400/05/05') to Gregorian date"""
    if pd.isna(date_str) or not date_str:
        return None
    
    try:
        # Remove any whitespace
        date_str = str(date_str).strip()
        # Parse Persian date and convert to Gregorian
        persian_date = jdatetime.datetime.strptime(date_str, '%Y/%m/%d')
        return persian_date.togregorian().date()
    except Exception as e:
        print(f"  [WARNING] Invalid date format: {date_str} - {e}")
        return None


def import_contracts():
    """Import contracts from Excel file"""
    
    # Drop contracts table with CASCADE to handle FK dependencies
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS contracts CASCADE"))
    print("[OK] Dropped contracts table with CASCADE")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
    
    # Read Excel file
    excel_path = "data/Contracts.xlsx"
    print(f"Reading Excel from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"[OK] Loaded {len(df)} rows from Excel")
    except FileNotFoundError:
        print(f"[ERROR] Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading Excel: {e}")
        return
    
    print(f"Excel has {len(df.columns)} columns")
    
    # Column mapping (Persian headers to model fields)
    column_mapping = {
        'کد رهگیری': 'tracking_code',
        'شماره طبقه بندی': 'employer_code',
        'شناسه ملی موسسه': 'university_id',
        'کد ملی فناور': 'researcher_id',
        'شناسه پیشنهاده': 'proposal_id',
        'شماره قرارداد': 'contract_number',
        'تاریخ قرارداد': 'contract_date',
        'مبلغ قرارداد(ریال)': 'total_amount',
        'عنوان قرارداد': 'title',
        'مدت زمان اجرا (ماه)': 'duration_months',
        'وضعیت': 'status'
    }
    
    # Start database session
    session = Session(bind=engine)
    
    try:
        # Performance optimization: Query all valid FK values once (avoid N+1)
        print("Fetching valid foreign key references...")
        
        valid_employer_codes = set(
            code for (code,) in session.query(Employer.classification_code).all()
        )
        print(f"[OK] Found {len(valid_employer_codes)} valid employer codes")
        
        valid_university_ids = set(
            uid for (uid,) in session.query(University.national_id).all()
        )
        print(f"[OK] Found {len(valid_university_ids)} valid university IDs")
        
        valid_researcher_ids = set(
            rid for (rid,) in session.query(Researcher.national_code).all()
        )
        print(f"[OK] Found {len(valid_researcher_ids)} valid researcher IDs")
        
        # Query existing tracking codes to avoid duplicates
        existing_tracking_codes = set(
            code for (code,) in session.query(Contract.tracking_code).all()
        )
        print(f"[OK] Found {len(existing_tracking_codes)} existing contracts in database")
        
        # Counters
        added_count = 0
        skipped_duplicate = 0
        skipped_fk_employer = 0
        skipped_fk_university = 0
        skipped_fk_researcher = 0
        skipped_invalid = 0
        error_count = 0
        
        print("\nProcessing records...")
        
        # Iterate through dataframe
        for index, row in df.iterrows():
            try:
                # Get tracking_code (primary key)
                tracking_code = row.get('کد رهگیری')
                
                # Convert pandas NaN to None and strip whitespaces
                tracking_code = None if pd.isna(tracking_code) else str(tracking_code).strip()
                
                # Skip if tracking_code is empty or already exists
                if not tracking_code:
                    skipped_invalid += 1
                    continue
                    
                if tracking_code in existing_tracking_codes:
                    skipped_duplicate += 1
                    continue
                
                # Get and validate FKs
                employer_code = row.get('شماره طبقه بندی')
                employer_code = None if pd.isna(employer_code) else str(employer_code).strip()
                
                university_id = row.get('شناسه ملی موسسه')
                university_id = None if pd.isna(university_id) else str(university_id).strip()
                
                researcher_id = row.get('کد ملی فناور')
                researcher_id = None if pd.isna(researcher_id) else str(researcher_id).strip()
                
                # Validate FK integrity - skip row if any FK is invalid
                if not employer_code or employer_code not in valid_employer_codes:
                    skipped_fk_employer += 1
                    if employer_code:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid employer_code '{employer_code}'")
                    continue
                
                if not university_id or university_id not in valid_university_ids:
                    skipped_fk_university += 1
                    if university_id:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid university_id '{university_id}'")
                    continue
                
                if not researcher_id or researcher_id not in valid_researcher_ids:
                    skipped_fk_researcher += 1
                    if researcher_id:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid researcher_id '{researcher_id}'")
                    continue
                
                # Prepare contract data
                contract_data = {
                    'tracking_code': tracking_code,
                    'employer_code': employer_code,
                    'university_id': university_id,
                    'researcher_id': researcher_id
                }
                
                # Map other fields
                for persian_col, field_name in column_mapping.items():
                    if field_name in ['tracking_code', 'employer_code', 'university_id', 'researcher_id']:
                        continue  # Already handled
                    
                    value = row.get(persian_col)
                    
                    # Handle date conversion
                    if field_name == 'contract_date':
                        contract_data[field_name] = parse_persian_date(value)
                    # Handle numeric fields
                    elif field_name == 'total_amount':
                        if pd.isna(value):
                            contract_data[field_name] = 0
                        else:
                            try:
                                contract_data[field_name] = Decimal(str(value))
                            except:
                                contract_data[field_name] = 0
                    elif field_name == 'duration_months':
                        if pd.isna(value):
                            contract_data[field_name] = None
                        else:
                            try:
                                contract_data[field_name] = int(value)
                            except:
                                contract_data[field_name] = None
                    # Handle strings
                    else:
                        if pd.isna(value):
                            contract_data[field_name] = None
                        elif isinstance(value, str):
                            contract_data[field_name] = value.strip()
                        else:
                            contract_data[field_name] = str(value)
                
                # Validate required fields
                if not contract_data.get('title'):
                    skipped_invalid += 1
                    continue
                
                # Set defaults for nullable fields
                if contract_data.get('status') is None:
                    contract_data['status'] = 'Active'
                
                # Create Contract instance
                contract = Contract(**contract_data)
                session.add(contract)
                
                # Add to existing set to prevent duplicates in same batch
                existing_tracking_codes.add(tracking_code)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    session.commit()
                    print(f"  Progress: {added_count} contracts added")
                
            except Exception as e:
                error_count += 1
                print(f"  [ERROR] Row {index + 1}: {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"[OK] Successfully imported: {added_count} contracts")
        print(f"[SKIP] Duplicates/empty tracking codes: {skipped_duplicate + skipped_invalid}")
        print(f"[FK_SKIP] Invalid employer_code: {skipped_fk_employer}")
        print(f"[FK_SKIP] Invalid university_id: {skipped_fk_university}")
        print(f"[FK_SKIP] Invalid researcher_id: {skipped_fk_researcher}")
        total_fk_skips = skipped_fk_employer + skipped_fk_university + skipped_fk_researcher
        print(f"[FK_SKIP] Total FK mismatches: {total_fk_skips}")
        print(f"[ERROR] Processing errors: {error_count}")
        print(f"Total rows processed: {len(df)}")
        print("="*60)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("="*60)
    print("CONTRACT IMPORT SCRIPT")
    print("="*60)
    import_contracts()


## File: scripts\import_deposits.py
------------------------------
import os
import sys
from pathlib import Path
from datetime import date
import shutil

import pandas as pd

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.employer import Employer
from models.deposits import AnnualMandate, DepositReceipt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Budget.xlsx"
TEMP_FILE_PATH = Path("C:/Temp/Budget_temp.xlsx")

# Unit conversion: Excel values are in Billion Rials, convert to base Rials
BILLION = 1_000_000_000


def normalize_code(value):
    """Normalize employer code by removing .0 suffix from numeric strings."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        return value[:-2]
    return value


def extract_year_from_column(col_name):
    """Extract integer year from Persian column names like 'سال 1398' or 'واریزی 1402'."""
    parts = col_name.split()
    for part in parts:
        if part.isdigit():
            return int(part)
    raise ValueError(f"Could not extract year from column: {col_name}")


def load_and_transform_budgets(file_path: Path):
    """Load both sheets and transform from wide to long format."""
    
    print(f"Reading Excel file: {file_path}")
    
    # Read Assigned_Budgets sheet
    assigned_df = pd.read_excel(file_path, sheet_name='Assigned_Budgets', engine='openpyxl')
    print(f"Loaded {len(assigned_df)} rows from Assigned_Budgets sheet")
    print(f"Column count: {len(assigned_df.columns)}")
    
    # Read Deposit_Budget sheet
    deposit_df = pd.read_excel(file_path, sheet_name='Deposit_Budget', engine='openpyxl')
    print(f"Loaded {len(deposit_df)} rows from Deposit_Budget sheet")
    print(f"Column count: {len(deposit_df.columns)}")
    
    # Transform Assigned_Budgets: wide to long
    code_col = 'شماره طبقه بندی'
    year_cols_assigned = [col for col in assigned_df.columns if col.startswith('سال')]
    
    assigned_long = pd.melt(
        assigned_df,
        id_vars=[code_col],
        value_vars=year_cols_assigned,
        var_name='year_column',
        value_name='mandated_amount'
    )
    assigned_long['fiscal_year'] = assigned_long['year_column'].apply(extract_year_from_column)
    assigned_long['employer_code'] = assigned_long[code_col].apply(normalize_code)
    assigned_long = assigned_long[['employer_code', 'fiscal_year', 'mandated_amount']]
    assigned_long['mandated_amount'] = pd.to_numeric(assigned_long['mandated_amount'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    assigned_long['mandated_amount'] = assigned_long['mandated_amount'] * BILLION
    
    print(f"Transformed Assigned_Budgets to {len(assigned_long)} long-format rows (scaled to base Rials)")
    
    # Transform Deposit_Budget: wide to long
    year_cols_deposit = [col for col in deposit_df.columns if col.startswith('واریزی')]
    
    deposit_long = pd.melt(
        deposit_df,
        id_vars=[code_col],
        value_vars=year_cols_deposit,
        var_name='year_column',
        value_name='deposited_amount'
    )
    deposit_long['fiscal_year'] = deposit_long['year_column'].apply(extract_year_from_column)
    deposit_long['employer_code'] = deposit_long[code_col].apply(normalize_code)
    deposit_long = deposit_long[['employer_code', 'fiscal_year', 'deposited_amount']]
    deposit_long['deposited_amount'] = pd.to_numeric(deposit_long['deposited_amount'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    #deposit_long['deposited_amount'] = deposit_long['deposited_amount'] * BILLION
    
    print(f"Transformed Deposit_Budget to {len(deposit_long)} long-format rows (scaled to base Rials)")
    
    # Merge on employer_code and fiscal_year (outer join)
    merged_df = pd.merge(
        assigned_long,
        deposit_long,
        on=['employer_code', 'fiscal_year'],
        how='outer'
    )
    merged_df['mandated_amount'] = merged_df['mandated_amount'].fillna(0)
    merged_df['deposited_amount'] = merged_df['deposited_amount'].fillna(0)
    
    print(f"Merged DataFrame has {len(merged_df)} rows")
    
    return merged_df


def persian_date_to_gregorian(year, month, day):
    """
    Simplified Persian to Gregorian conversion.
    For MVP purposes, we'll use a simple approximation:
    Persian year Y maps roughly to Gregorian year Y+621 or Y+622.
    The last day of Persian year (12/29) is around March 20.
    """
    gregorian_year = year + 621
    return date(gregorian_year, 3, 20)


def import_deposits(file_path: Path = EXCEL_FILE_PATH):
    """Main ETL function: Extract, Transform, Load deposit data."""
    
    # Drop existing tables in correct order (child first, then parent)
    print("Dropping existing deposit tables...")
    DepositReceipt.__table__.drop(engine, checkfirst=True)
    AnnualMandate.__table__.drop(engine, checkfirst=True)
    print("Tables dropped successfully.")
    
    # Recreate schema
    print("Recreating deposit tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    # Use temp file if original is locked - check before attempting to use
    if TEMP_FILE_PATH.exists():
        actual_file = TEMP_FILE_PATH
        print(f"Using temp file: {actual_file}")
    else:
        actual_file = file_path
        print(f"Using original file: {actual_file}")
    
    # Load and transform data
    merged_df = load_and_transform_budgets(actual_file)
    
    # Get valid employer codes from database
    db = SessionLocal()
    try:
        valid_codes = {emp.classification_code for emp in db.query(Employer.classification_code).all()}
        print(f"Found {len(valid_codes)} valid employer codes in database")
        
        mandates_added = 0
        receipts_added = 0
        skipped_missing_employer = 0
        
        for idx, row in merged_df.iterrows():
            employer_code = row['employer_code']
            fiscal_year = int(row['fiscal_year'])
            mandated_amount = float(row['mandated_amount'])
            deposited_amount = float(row['deposited_amount'])
            
            # Skip if employer doesn't exist
            if employer_code not in valid_codes:
                if skipped_missing_employer < 5:  # Only log first 5
                    print(f"WARNING: Skipping row {idx} - employer_code '{employer_code}' not found in database")
                skipped_missing_employer += 1
                continue
            
            # Create Annual_Mandate record
            mandate = AnnualMandate(
                employer_code=employer_code,
                fiscal_year=fiscal_year,
                mandated_amount=mandated_amount
            )
            db.add(mandate)
            mandates_added += 1
            
            # Create Deposit_Receipt if deposited_amount > 0
            if deposited_amount > 0:
                deposit_date = persian_date_to_gregorian(fiscal_year, 12, 29)
                receipt = DepositReceipt(
                    employer_code=employer_code,
                    fiscal_year=fiscal_year,
                    deposit_amount=deposited_amount,
                    deposit_date=deposit_date,
                    description='Historical Aggregated Deposit'
                )
                db.add(receipt)
                receipts_added += 1
        
        # Commit transaction
        db.commit()
        print("\n=== Import Summary ===")
        print(f"Successfully imported {mandates_added} Annual_Mandate records")
        print(f"Successfully imported {receipts_added} Deposit_Receipt records")
        print(f"Skipped {skipped_missing_employer} rows due to missing employer codes")
        print(f"\nNote: All monetary values converted from Billion Rials to base Rials (×{BILLION:,})")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_deposits()


## File: scripts\import_employers.py
------------------------------
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from core.database import Base, SessionLocal, engine
from models.employer import Employer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Employers.xlsx"

COLUMN_MAPPING = {
    "شماره طبقه بندی": "classification_code",
    "نام مشمول": "name",
    "نوع مشمول": "employer_type",
    "شماره طبقه بندی سازمان مادر": "parent_code",
    "استان": "province",
    "عنوان امور": "affairs_category",
    "دستگاه اجرایی بالادست": "upper_organization",
    "وضعیت فعالیت": "status",
}

EMPLOYER_TYPE_MAPPING = {
    "مادر": "Mother",
    "زیرمجموعه": "Subsidiary",
    "مستقل": "Independent",
}

STATUS_MAPPING = {
    "فعال": "Active",
    "غیرفعال": "Inactive",
}

UNKNOWN_REQUIRED_VALUE = "Unknown"


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value).strip()


def normalize_code(value):
    value = clean_value(value)
    if value is None:
        return None
    if value.endswith(".0"):
        return value[:-2]
    return value


def normalize_employer_type(value):
    value = clean_value(value)
    return EMPLOYER_TYPE_MAPPING.get(value, value)


def normalize_status(value):
    value = clean_value(value)
    if value is None:
        return "Active"
    return STATUS_MAPPING.get(value, value)


def load_employers_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing Excel columns: {sorted(missing_columns)}")
    df = df.rename(columns=COLUMN_MAPPING)
    return df.where(pd.notnull(df), None)


def build_employer(row) -> Employer:
    classification_code = normalize_code(row["classification_code"])
    if classification_code is None:
        raise ValueError("classification_code is required")

    return Employer(
        classification_code=classification_code,
        name=clean_value(row["name"]) or UNKNOWN_REQUIRED_VALUE,
        employer_type=normalize_employer_type(row["employer_type"]),
        parent_code=normalize_code(row["parent_code"]),
        province=clean_value(row["province"]) or UNKNOWN_REQUIRED_VALUE,
        affairs_category=clean_value(row["affairs_category"]),
        upper_organization=clean_value(row["upper_organization"]) or UNKNOWN_REQUIRED_VALUE,
        status=normalize_status(row["status"]),
    )


def import_employers(file_path: Path = EXCEL_FILE_PATH) -> None:
    # Force drop the table and all its dependents
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS employers CASCADE"))
    Base.metadata.create_all(bind=engine)

    print(f"Reading Excel file: {file_path}")
    df = load_employers_dataframe(file_path)
    print(f"Loaded {len(df)} rows from Excel.")

    db = SessionLocal()
    records_added = 0
    duplicates_skipped = 0

    try:
        for index, row in df.iterrows():
            employer = build_employer(row)

            existing_employer = (
                db.query(Employer)
                .filter_by(classification_code=employer.classification_code)
                .first()
            )
            if existing_employer:
                duplicates_skipped += 1
                print(f"Skipping duplicate: {employer.classification_code}")
                continue

            db.add(employer)
            records_added += 1

        db.commit()
        print("Import committed successfully.")
        print(f"Successfully imported {records_added} new employers.")
        print(f"Skipped {duplicates_skipped} existing employers.")
    except Exception:
        db.rollback()
        print("Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_employers()


## File: scripts\import_payments.py
------------------------------
import sys
import os
from datetime import datetime, date

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import jdatetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import engine, Base
from models.payment import Payment
from models.contract import Contract


def parse_jalali_date(date_str):
    """Convert Jalali date string (YYYY/MM/DD) to Gregorian date object."""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    
    try:
        date_str = str(date_str).strip()
        parts = date_str.split('/')
        if len(parts) != 3:
            return None
        
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        jalali_date = jdatetime.date(year, month, day)
        gregorian_date = jalali_date.togregorian()
        return gregorian_date
    except (ValueError, AttributeError, IndexError):
        return None


def clean_numeric(value):
    """Remove commas from numeric strings and convert to int."""
    if pd.isna(value):
        return 0
    
    try:
        # Convert to string, remove commas, then to int
        cleaned = str(value).replace(',', '').strip()
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0


def main():
    print("Starting Payments import...")
    
    # Read Excel file
    print("\n1. Reading Excel file...")
    df = pd.read_excel('data/Payments.xlsx')
    print(f"   Loaded {len(df)} rows from Excel")
    
    # Display column names for verification
    print(f"\n   Columns found: {df.columns.tolist()}")
    
    # Expected Persian headers
    expected_cols = [
        'سری پرداخت',
        'کد رهگیری پرداخت', 
        'کد رهگیری',
        'مبلغ پرداختی(ریال)',
        'شماره نامه ابلاغ',
        'تاریخ ابلاغ',
        'سال پرداخت',
        'پرداخت از محل سال مالی'
    ]
    
    # Verify all expected columns exist
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"\n   WARNING: Missing columns: {missing_cols}")
        return
    
    # Drop table and recreate
    print("\n2. Dropping existing payments table...")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS payments CASCADE"))
    
    print("   Creating fresh payments table...")
    Base.metadata.create_all(bind=engine, tables=[Payment.__table__])
    
    # Fetch valid contract tracking codes
    print("\n3. Fetching valid contract tracking codes...")
    session = Session(bind=engine)
    try:
        valid_contracts = set(session.query(Contract.tracking_code).all())
        valid_contracts = {code[0] for code in valid_contracts}
        print(f"   Found {len(valid_contracts)} valid contracts")
    finally:
        session.close()
    
    # Process payments
    print("\n4. Processing payment records...")
    session = Session(bind=engine)
    
    inserted_count = 0
    skipped_count = 0
    skipped_reasons = []
    
    try:
        for idx, row in df.iterrows():
            # Extract values
            tracking_code = str(row['کد رهگیری پرداخت']).strip() if pd.notna(row['کد رهگیری پرداخت']) else None
            contract_tracking_code = str(row['کد رهگیری']).strip() if pd.notna(row['کد رهگیری']) else None
            series = str(row['سری پرداخت']).strip() if pd.notna(row['سری پرداخت']) else None
            amount = clean_numeric(row['مبلغ پرداختی(ریال)'])
            notification_letter_number = str(row['شماره نامه ابلاغ']).strip() if pd.notna(row['شماره نامه ابلاغ']) else None
            notification_date = parse_jalali_date(row['تاریخ ابلاغ'])
            payment_year = int(row['سال پرداخت']) if pd.notna(row['سال پرداخت']) else None
            funding_year = int(row['پرداخت از محل سال مالی']) if pd.notna(row['پرداخت از محل سال مالی']) else None
            
            # Validate required fields
            if not tracking_code:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing tracking_code")
                continue
            
            if not contract_tracking_code:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing contract_tracking_code")
                continue
            
            # Validate FK integrity
            if contract_tracking_code not in valid_contracts:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Contract '{contract_tracking_code}' not found")
                continue
            
            if not payment_year or not funding_year:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing payment_year or funding_year")
                continue
            
            # Create Payment instance
            payment = Payment(
                tracking_code=tracking_code,
                contract_tracking_code=contract_tracking_code,
                series=series,
                amount=amount,
                notification_letter_number=notification_letter_number,
                notification_date=notification_date,
                payment_year=payment_year,
                funding_year=funding_year,
                attachment_path=None
            )
            
            session.add(payment)
            inserted_count += 1
        
        # Commit all changes
        session.commit()
        print(f"\n✓ Successfully inserted {inserted_count} payments")
        
        if skipped_count > 0:
            print(f"\n⚠ Skipped {skipped_count} rows due to validation errors:")
            for reason in skipped_reasons[:10]:  # Show first 10
                print(f"   - {reason}")
            if len(skipped_reasons) > 10:
                print(f"   ... and {len(skipped_reasons) - 10} more")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error during import: {e}")
        raise
    finally:
        session.close()
    
    print("\n" + "="*50)
    print("Payment import completed!")
    print(f"Total rows processed: {len(df)}")
    print(f"Successfully inserted: {inserted_count}")
    print(f"Skipped: {skipped_count}")
    print("="*50)


if __name__ == '__main__':
    main()


## File: scripts\import_researchers.py
------------------------------
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.researchers import Researcher
from models.university import University
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Researchers.xlsx"

COLUMN_MAPPING = {
    "کد رهگیری فناور": "tracking_code",
    "کد ملی فناور": "national_code",
    "نام فناور": "first_name",
    "نام خانوادگی فناور": "last_name",
    "تلفن همراه": "mobile",
    "ایمیل": "email",
    "درجه علمی": "academic_rank",
    "شناسه ملی موسسه": "university_id",
    "مدرک تحصیلی": "education_level",
    "نوع فناور": "researcher_type",
    "وضعیت": "status",
}

STATUS_MAPPING = {
    "فعال": "Active",
    "غیرفعال": "Inactive",
}


def clean_value(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value or None


def normalize_status(value):
    value = clean_value(value)
    if value is None:
        return "Active"
    return STATUS_MAPPING.get(value, value)


def load_researchers_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing Excel columns: {sorted(missing_columns)}")
    df = df.rename(columns=COLUMN_MAPPING)
    return df.where(pd.notnull(df), None)


def build_researcher(row) -> Researcher | None:
    national_code = clean_value(row["national_code"])
    if national_code is None:
        return None

    first_name = clean_value(row["first_name"])
    last_name = clean_value(row["last_name"])

    return Researcher(
        national_code=national_code,
        tracking_code=clean_value(row["tracking_code"]),
        first_name=first_name or "Unknown",
        last_name=last_name or "Unknown",
        full_name=f"{first_name or 'Unknown'} {last_name or 'Unknown'}",
        mobile=clean_value(row["mobile"]),
        email=clean_value(row["email"]),
        academic_rank=clean_value(row["academic_rank"]),
        university_id=clean_value(row["university_id"]),
        education_level=clean_value(row["education_level"]),
        researcher_type=clean_value(row["researcher_type"]),
        status=normalize_status(row["status"]),
    )


def import_researchers(file_path: Path = EXCEL_FILE_PATH) -> None:
    # Force drop the table and all its dependents (e.g., contracts)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS researchers CASCADE"))
    Base.metadata.create_all(bind=engine)

    print(f"Reading Excel file: {file_path}")
    df = load_researchers_dataframe(file_path)
    print(f"Loaded {len(df)} rows from Excel.")

    db = SessionLocal()
    records_added = 0
    missing_national_code_skipped = 0
    invalid_university_skipped = 0
    duplicate_skipped = 0
    seen_national_codes = set()

    try:
        valid_universities = {
            national_id for (national_id,) in db.query(University.national_id).all()
        }
        print(f"Loaded {len(valid_universities)} valid universities for FK checks.")

        for index, row in df.iterrows():
            researcher = build_researcher(row)
            if researcher is None:
                missing_national_code_skipped += 1
                continue

            if researcher.national_code in seen_national_codes:
                duplicate_skipped += 1
                print(f"Row {index + 2}: skipping duplicate national_code {researcher.national_code}")
                continue

            if researcher.university_id not in valid_universities:
                invalid_university_skipped += 1
                print(
                    f"Row {index + 2}: skipping researcher {researcher.national_code}; "
                    f"invalid university_id {researcher.university_id}"
                )
                continue

            db.add(researcher)
            seen_national_codes.add(researcher.national_code)
            records_added += 1

        db.commit()
        print("Import committed successfully.")
        print(f"Successfully imported {records_added} researchers.")
        print(f"Skipped {missing_national_code_skipped} rows without national_code.")
        print(f"Skipped {invalid_university_skipped} rows with invalid university_id.")
        print(f"Skipped {duplicate_skipped} duplicate researchers.")
    except Exception:
        db.rollback()
        print("Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_researchers()


## File: scripts\import_universities.py
------------------------------
import pandas as pd
import sys
from pathlib import Path
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from models.university import University


def import_universities():
    """Import universities from Excel file"""
    
    # Drop universities table with CASCADE to handle FK dependencies
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS universities CASCADE"))
    print("[OK] Dropped universities table with CASCADE")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
    
    # Read Excel file
    excel_path = "data/Universities.xlsx"
    print(f"Reading Excel from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        print(f"[OK] Loaded {len(df)} rows from Excel")
    except FileNotFoundError:
        print(f"[ERROR] Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading Excel: {e}")
        return
    
    # Display column count (avoid printing Persian characters)
    print(f"Excel has {len(df.columns)} columns")
    
    # Column mapping (Persian headers to model fields)
    column_mapping = {
        'کد رهگیری': 'tracking_code',
        'شناسه ملی موسسه': 'national_id',
        'نام موسسه': 'name',
        'شهر': 'city',
        'آدرس': 'address',
        'استان موسسه': 'province',
        'نوع موسسه': 'university_type',
        'وضعیت': 'status'
    }
    
    # Start database session
    session = Session(bind=engine)
    
    try:
        # Performance optimization: Query existing national_ids once
        print("Fetching existing university records...")
        existing_ids = set(
            national_id for (national_id,) in session.query(University.national_id).all()
        )
        print(f"[OK] Found {len(existing_ids)} existing universities in database")
        
        # Counters
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        print("\nProcessing records...")
        
        # Iterate through dataframe
        for index, row in df.iterrows():
            try:
                # Get national_id (primary key)
                national_id = row.get('شناسه ملی موسسه')
                
                # Convert pandas NaN to None and strip whitespaces
                national_id = None if pd.isna(national_id) else str(national_id).strip()
                
                # Skip if national_id is empty or already exists
                if not national_id:
                    skipped_count += 1
                    continue
                    
                if national_id in existing_ids:
                    skipped_count += 1
                    continue
                
                # Prepare university data
                university_data = {}
                for persian_col, field_name in column_mapping.items():
                    value = row.get(persian_col)
                    # Convert NaN to None, strip strings
                    if pd.isna(value):
                        university_data[field_name] = None
                    elif isinstance(value, str):
                        university_data[field_name] = value.strip()
                    else:
                        university_data[field_name] = value
                
                # Handle NOT NULL constraints - provide defaults for required fields
                # If university_type is None, set a default value
                if university_data.get('university_type') is None:
                    university_data['university_type'] = 'نامشخص'
                
                # If province is None, set a default value
                if university_data.get('province') is None:
                    university_data['province'] = 'نامشخص'
                
                # If name is None, skip this record
                if university_data.get('name') is None:
                    skipped_count += 1
                    continue
                
                # If status is None, set default
                if university_data.get('status') is None:
                    university_data['status'] = 'فعال'
                
                # Create University instance
                university = University(**university_data)
                session.add(university)
                
                # Add to existing_ids set to prevent duplicates in same batch
                existing_ids.add(national_id)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    session.commit()
                    print(f"  Progress: {added_count} universities added, {skipped_count} skipped")
                
            except Exception as e:
                error_count += 1
                print(f"  Row {index + 1}: Error - {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"[OK] Successfully imported: {added_count} universities")
        print(f"[SKIP] Skipped (duplicates/empty): {skipped_count}")
        print(f"[ERROR] Errors: {error_count}")
        print(f"Total rows processed: {len(df)}")
        print("="*60)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("="*60)
    print("UNIVERSITY IMPORT SCRIPT")
    print("="*60)
    import_universities()


## File: scripts\process_budgets.py
------------------------------
import re
import pandas as pd
from pathlib import Path

# ==========================================
# Configuration and Constants
# ==========================================
# Defining absolute paths using pathlib for Windows compatibility
BASE_DIR = Path(r"C:\Users\pchin\OneDrive\AI-Project\SATE_Fin_Dev\data")
INPUT_EXCEL_FILE = BASE_DIR / "Budget.xlsx"
OUTPUT_EXCEL_FILE = BASE_DIR / "Budget_longformat.xlsx"

ASSIGNED_SHEET_NAME = "Assigned_Budgets"
DEPOSIT_SHEET_NAME = "Deposit_Budget"
EMPLOYER_CODE_COL = "شماره طبقه بندی"

def clean_employer_code(value: str) -> str:
    """
    Normalizes the employer code by stripping whitespaces and removing trailing '.0'.
    Returns None if the value is invalid or empty.
    """
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def clean_financial_amount(value: str) -> float:
    """
    Cleans financial amount strings (removes commas, handles empty strings) 
    and converts them to float. Prevents calculation errors by returning 0.0 for blanks.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value:
            return 0.0
    return pd.to_numeric(value, errors="coerce")

def extract_fiscal_year(column_name: str) -> int:
    """
    Extracts the 4-digit fiscal year from a given column header.
    Raises ValueError if no year is found, preventing silent data corruption.
    """
    match = re.search(r"(\d{4})", str(column_name))
    if not match:
        raise ValueError(f"CRITICAL: Could not extract fiscal year from: {column_name}")
    return int(match.group(1))

def process_budget_data() -> None:
    """
    Main ETL pipeline: Reads multi-sheet Excel safely, melts data to long format,
    applies business logic, and exports to the exact target directory.
    """
    # 1. Validate Directory Existence
    if not BASE_DIR.exists():
        print(f"Error: The directory {BASE_DIR} does not exist.")
        return

    # 2. Read Excel File using ExcelFile for atomic loading and performance
    print(f"Loading data from: {INPUT_EXCEL_FILE}")
    try:
        with pd.ExcelFile(INPUT_EXCEL_FILE) as xls:
            df_assigned_wide = pd.read_excel(xls, sheet_name=ASSIGNED_SHEET_NAME)
            df_deposit_wide = pd.read_excel(xls, sheet_name=DEPOSIT_SHEET_NAME)
    except FileNotFoundError:
        print(f"Error: The file {INPUT_EXCEL_FILE} was not found.")
        return
    except ValueError as e:
        print(f"Error reading sheets: {e}")
        return

    # 3. Process Assigned Budgets (Mandates)
    print("Processing Assigned Budgets...")
    df_assigned_long = pd.melt(
        df_assigned_wide,
        id_vars=[EMPLOYER_CODE_COL],
        var_name="Year_Raw",
        value_name="Assigned_Amount"
    )
    df_assigned_long["Fiscal_Year"] = df_assigned_long["Year_Raw"].apply(extract_fiscal_year)
    df_assigned_long[EMPLOYER_CODE_COL] = df_assigned_long[EMPLOYER_CODE_COL].apply(clean_employer_code)
    #df_assigned_long["Assigned_Amount"] = df_assigned_long["Assigned_Amount"].apply(clean_financial_amount)
    df_assigned_long["Assigned_Amount"] = df_assigned_long["Assigned_Amount"].apply(clean_financial_amount) * 1_000_000_000
    
    # Implementing Soft Delete mechanism for database mapping
    df_assigned_long["Is_Deleted"] = False
    df_assigned_long.drop(columns=["Year_Raw"], inplace=True)

    # 4. Process Deposit Budgets
    print("Processing Deposit Budgets...")
    df_deposit_long = pd.melt(
        df_deposit_wide,
        id_vars=[EMPLOYER_CODE_COL],
        var_name="Year_Raw",
        value_name="Deposit_Amount"
    )
    df_deposit_long["Fiscal_Year"] = df_deposit_long["Year_Raw"].apply(extract_fiscal_year)
    df_deposit_long[EMPLOYER_CODE_COL] = df_deposit_long[EMPLOYER_CODE_COL].apply(clean_employer_code)
    df_deposit_long["Deposit_Amount"] = df_deposit_long["Deposit_Amount"].apply(clean_financial_amount)
    
    # Implementing Soft Delete mechanism
    df_deposit_long["Is_Deleted"] = False
    df_deposit_long.drop(columns=["Year_Raw"], inplace=True)

    # 5. Merge Data securely to prevent data loss (Outer Join)
    print("Merging data...")
    df_merged = pd.merge(
        df_assigned_long,
        df_deposit_long,
        on=[EMPLOYER_CODE_COL, "Fiscal_Year"],
        how="outer",
        suffixes=("_assigned", "_deposit")
    )
    
    # Resolving data nulls after outer merge to maintain mathematical accuracy
    df_merged["Is_Deleted"] = False 
    df_merged["Assigned_Amount"] = df_merged["Assigned_Amount"].fillna(0.0)
    df_merged["Deposit_Amount"] = df_merged["Deposit_Amount"].fillna(0.0)
    
    # Clean up: Remove rows where there is absolutely no financial activity
    df_merged = df_merged[(df_merged["Assigned_Amount"] > 0) | (df_merged["Deposit_Amount"] > 0)]

    # 6. Export to Excel in target directory
    print(f"Exporting processed data to: {OUTPUT_EXCEL_FILE}")
    with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine='xlsxwriter') as writer:
        df_merged.to_excel(writer, sheet_name='Merged_Master_Data', index=False)
        df_assigned_long.to_excel(writer, sheet_name='Assigned_LongFormat', index=False)
        df_deposit_long.to_excel(writer, sheet_name='Deposit_LongFormat', index=False)
    
    print("Data processing complete. Data integrity maintained.")

if __name__ == "__main__":
    process_budget_data()

## File: scripts\verify_universities.py
------------------------------
import sys
from pathlib import Path
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import engine
from models.university import University

session = Session(bind=engine)

# Get total count
total = session.query(University).count()
print(f"Total universities in database: {total}")

# Get sample records
print("\nSample records:")
print("-" * 80)
for uni in session.query(University).limit(5):
    print(f"National ID: {uni.national_id}")
    print(f"Name: {uni.name}")
    print(f"Type: {uni.university_type}")
    print(f"Province: {uni.province}")
    print(f"Status: {uni.status}")
    print("-" * 80)

session.close()


## File: services\financial_engine.py
------------------------------
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from decimal import Decimal

# Import models from the root-level 'models' directory
from models.employer import Employer
from models.deposits import DepositReceipt
from models.contract import Contract
from models.payment import Payment

def calculate_real_balance(db: Session, employer_code: str, funding_year: int) -> float:
    """
    Calculates the real financial balance for a specific employer and funding year.
    Formula: Sum of deposits (self + subsidiaries) - Sum of payments linked to employer's contracts for the specified funding_year.
    """
    
    # 1. Calculate Total Deposits (Including subsidiaries)
    # Finding the employer and all its subsidiaries using the parent_code constraint
    deposits_query = db.query(func.sum(DepositReceipt.deposit_amount)).join(
        Employer, DepositReceipt.employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code
        ),
        DepositReceipt.fiscal_year == funding_year,
        DepositReceipt.is_deleted == False,
        Employer.is_deleted == False
    ).scalar()
    
    total_deposits = deposits_query or Decimal('0.0')

    # 2. Calculate Total Payments based on funding_year (NOT payment_year)
    payments_query = db.query(func.sum(Payment.amount)).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code == employer_code,
        Payment.funding_year == funding_year,
        Payment.is_deleted == False,
        Contract.is_deleted == False
    ).scalar()

    total_payments = payments_query or Decimal('0.0')

    # 3. Calculate Real Balance
    real_balance = total_deposits - total_payments
    
    return float(real_balance)

def get_mandated_amount(db: Session, employer_code: str, fiscal_year: int) -> float:
    """
    Retrieves the mandated budget amount (اعتبار تکلیفی) for a specific employer.
    """
    from models.deposits import AnnualMandate
    
    mandate = db.query(AnnualMandate).filter(
        AnnualMandate.employer_code == employer_code,
        AnnualMandate.fiscal_year == fiscal_year,
        AnnualMandate.is_deleted == False
    ).first()
    
    return float(mandate.mandated_amount) if mandate else 0.0

