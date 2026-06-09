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