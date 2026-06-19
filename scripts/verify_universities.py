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
