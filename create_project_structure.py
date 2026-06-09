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
