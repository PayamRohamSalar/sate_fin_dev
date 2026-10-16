"""Show the newest record already in the database for each SATE registry.

Run it BEFORE exporting from SATE to know from which date / code the new
export must start (see results/import_reports/Monthly_SATE_Import_StepByStep.md).

Usage: python scripts/addin_last_dates.py
"""

import io
import sys
from pathlib import Path

import jdatetime
from sqlalchemy import text

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal  # noqa: E402


def jalali(value) -> str:
    if value is None:
        return "-"
    day = value.date() if hasattr(value, "date") else value
    return str(jdatetime.date.fromgregorian(date=day)).replace("-", "/")


def main() -> None:
    db = SessionLocal()
    q = lambda sql: db.execute(text(sql)).fetchone()  # noqa: E731
    try:
        rows = [
            ("قراردادها",
             "select count(*), max(contract_date), "
             "max(case when tracking_code ~ '^[0-9]+$' then tracking_code::bigint end) "
             "from contracts where is_deleted=false"),
            ("تقاضاها",
             "select count(*), max(demand_date), "
             "max(case when tracking_code ~ '^[0-9]+$' then tracking_code::bigint end) "
             "from demands where is_deleted=false"),
            ("پیشنهاده‌ها",
             "select count(*), max(submitted_at), max(id) from proposals "
             "where is_deleted=false and submitted_at > '2000-01-01'"),
            ("فناوران (تاریخ ندارند؛ آخرین کد رهگیری)",
             "select count(*), null, "
             "max(case when tracking_code ~ '^[0-9]+$' then tracking_code::bigint end) "
             "from researchers where is_deleted=false"),
        ]
        print(f"{'جدول':<40}{'تعداد':>8}   {'آخرین تاریخ (شمسی)':<22}{'بزرگ‌ترین کد'}")
        print("-" * 90)
        for label, sql in rows:
            count, last_date, last_code = q(sql)
            print(f"{label:<40}{count:>8}   {jalali(last_date):<22}{last_code}")

        series = q(
            "select series from payments where is_deleted=false and series ~ '^05-[0-9]+$' "
            "order by series desc limit 1"
        )
        print(f"\nآخرین سری پرداخت ۱۴۰۵ در پایگاه داده: {series[0] if series else '-'}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
