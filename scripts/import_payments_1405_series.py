"""Bring ALL 1405 payment series (05-01 .. 05-30) in line with Payam's payment table.

Source: ``data/جدول پرداخت 1405_سری 30.xlsx`` (Sheet1). Columns, by position:
    سری | کد رهگیری پرداخت | متقاضی | کد طبقه‌بندی | دانشگاه | فناور | عنوان قرارداد |
    مبلغ کل قرارداد(ریال) | مبلغ درخواستی(ریال) | شماره نامه ابلاغ | تاریخ ابلاغ

What it does (2026-10-16)
-------------------------
1. Rows whose payment tracking code ("کد رهگیری پرداخت", the unique code of the
   progress report) is already in ``payments``:
   * series label, notification letter number and notification date are
     refreshed from the sheet (blank sheet cells never erase DB values);
   * ``payment_date`` follows the notification date wherever it was empty or
     equal to the old notification date (the convention of the earlier
     imports, where payment_date == notification date).
2. Rows missing from ``payments``: the contract is NOT in the sheet, so it is
   resolved from the descriptive fields (employer + total contract amount,
   title, university, researcher -- see ``contract_match.py`` logic below) and
   the payment is inserted. Convention of the earlier 1405 import
   (scripts/import_payments_1405.py): ``payment_year=1405``,
   ``funding_year=1404``, status ``Final``, execution_year / payment_type left
   empty, as on every existing 05-xx row.
3. Rows that cannot be imported (blank / "محرمانه" tracking code, no matching
   contract, ambiguous contract) are never guessed at: they are written to the
   report workbook for manual entry.

Data quirks handled
-------------------
* In a few series the letter-number and letter-date columns are swapped
  (the date sits in the number column); detected by pattern and put back.
* Employer codes ``1400278579`` / ``1400278580`` are the institute (128342) and
  ``1400860408`` is the Oil Ministry's code cut to 10 digits (14008604085).
* A blank tracking code is matched to an existing DB payment only when series,
  contract employer and amount identify exactly one DB row that the sheet does
  not otherwise mention (this is how the confidential Bushehr payment C_2273
  is recognised).

Usage:
    python scripts/import_payments_1405_series.py            # dry run
    python scripts/import_payments_1405_series.py --apply
"""

from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.database import SessionLocal  # noqa: E402
from core.date_helper import parse_strict_jalali_date  # noqa: E402
import models.contract, models.transfer  # noqa: E402,F401  (mapper registry)
from models.payment import Payment  # noqa: E402

SOURCE_FILE = ROOT / "data" / "جدول پرداخت 1405_سری 30.xlsx"
REPORT_PATH = ROOT / "results" / "payments_1405_series30_report.xlsx"
UNDO_PATH = ROOT / "results" / "payments_1405_series30_undo.json"

PAYMENT_YEAR = 1405
FUNDING_YEAR = 1404
LAST_PREVIOUSLY_IMPORTED_SERIES = 25  # series 05-26..05-30 are the new ones

COLUMNS = ["series", "pcode", "applicant", "emp_code", "university", "researcher", "title",
           "contract_total", "amount", "letter_no", "letter_date"]
DATE_RE = re.compile(r"^\d{4}/\d{2}/\d{2}$")
EMPLOYER_CODE_FIXES = {"1400278579": "128342", "1400278580": "128342", "1400860408": "14008604085"}
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


# ---------------------------------------------------------------- reading
def read_source() -> pd.DataFrame:
    """Read the sheet; works even while Excel holds the file open (shared read)."""
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / "payments.xlsx"
    try:
        with open(SOURCE_FILE, "rb") as src, open(tmp, "wb") as dst:
            shutil.copyfileobj(src, dst)
    except PermissionError:
        # Excel keeps the workbook locked while it is open; a shared-read handle still works on Windows.
        import os
        import subprocess
        script = (
            "$s=[System.IO.File]::Open($env:PAY_SRC,'Open','Read','ReadWrite');"
            "$d=[System.IO.File]::Create($env:PAY_DST);$s.CopyTo($d);$d.Close();$s.Close()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True,
                       env={**os.environ, "PAY_SRC": str(SOURCE_FILE), "PAY_DST": str(tmp)})
    df = pd.read_excel(tmp, sheet_name="Sheet1", dtype=str)
    df.columns = COLUMNS
    for col in df.columns:
        df[col] = df[col].map(lambda v: None if pd.isna(v) else str(v).strip())
    df["emp_code"] = df["emp_code"].map(lambda c: EMPLOYER_CODE_FIXES.get(c, c))
    # letter columns swapped in some series: date pattern sits in the number column
    swapped = df["letter_no"].fillna("").str.fullmatch(DATE_RE) & ~df["letter_date"].fillna("").str.fullmatch(DATE_RE) & df["letter_date"].notna()
    df.loc[swapped, ["letter_no", "letter_date"]] = df.loc[swapped, ["letter_date", "letter_no"]].values
    df = df.astype(object).where(df.notna(), None)  # NaN -> None again after the swap
    df["swapped"] = swapped
    df["tracking_ok"] = df["pcode"].fillna("").str.fullmatch(r"\d+")
    return df


def parse_date(value):
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return parse_strict_jalali_date(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------- contract matching
def norm(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    s = str(value).translate(PERSIAN_DIGITS)
    s = s.replace("ي", "ی").replace("ك", "ک").replace("ة", "ه").replace("‌", " ").replace("‏", "").replace("‎", "")
    s = re.sub(r"[\"'«»()\[\]{}،,.:;؛\-–—_/\\]+", " ", s)
    return " ".join(s.lower().split())


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def load_contracts(db):
    rows = db.execute(text("""
        select c.tracking_code, c.employer_code, c.total_amount, c.title, coalesce(u.name,''), coalesce(r.full_name,'')
        from contracts c left join universities u on u.national_id = c.university_id
                         left join researchers r on r.national_code = c.researcher_id
        where c.is_deleted = false""")).all()
    return [{"code": code, "emp": str(emp).strip(), "total": int(total), "title": norm(title),
             "uni": norm(uni), "res": norm(res)} for code, emp, total, title, uni, res in rows]


def match_contract(row, contracts):
    """(contract code | None, how/why, number of candidates)."""
    try:
        total = int(float(row["contract_total"]))
    except (TypeError, ValueError):
        return None, "مبلغ کل قرارداد در اکسل عددی نیست (محرمانه/خالی)", 0
    emp = row["emp_code"]
    title, uni, res = norm(row["title"]), norm(row["university"]), norm(row["researcher"])

    def narrow(cands):
        if len(cands) == 1:
            return cands[0], None
        exact = [c for c in cands if c["title"] == title]
        if len(exact) == 1:
            return exact[0], "عنوان"
        pool = exact or cands
        by_ur = [c for c in pool if c["uni"] == uni and (c["res"] == res or not res)]
        if len(by_ur) == 1:
            return by_ur[0], "عنوان/دانشگاه/فناور"
        scored = sorted(((ratio(c["title"], title), c) for c in pool), key=lambda x: -x[0])
        if scored and scored[0][0] >= 0.9 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.05):
            return scored[0][1], f"عنوان تقریبی ({scored[0][0]:.2f})"
        return None, None

    c1 = [c for c in contracts if c["emp"] == emp and c["total"] == total]
    if c1:
        hit, extra = narrow(c1)
        if hit:
            return hit["code"], "کارفرما+مبلغ" + (f"+{extra}" if extra else ""), len(c1)
        return None, f"{len(c1)} قرارداد با همین کارفرما و مبلغ؛ تفکیک با عنوان/دانشگاه/فناور ممکن نشد", len(c1)
    c2 = [c for c in contracts if c["total"] == total and (c["title"] == title or ratio(c["title"], title) >= 0.9)]
    if c2:
        hit, extra = narrow(c2)
        if hit:
            return hit["code"], "مبلغ+عنوان (کد کارفرما نامنطبق)", len(c2)
        return None, f"{len(c2)} قرارداد با همین مبلغ و عنوان مشابه", len(c2)
    c3 = [c for c in contracts if c["emp"] == emp and c["title"] == title and c["uni"] == uni and (c["res"] == res or not res)]
    if len(c3) == 1:
        return c3[0]["code"], "کارفرما+عنوان+دانشگاه+فناور (مبلغ کل متفاوت)", 1
    return None, "قراردادی با این مشخصات (کارفرما/مبلغ/عنوان/دانشگاه/فناور) در دیتابیس نیست", 0


# ------------------------------------------------------------------- main
def series_key(s: str):
    a, b = s.split("-")
    return int(a), int(b)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    df = read_source()
    print(f"ردیف‌های اکسل: {len(df)} | سری‌ها: {df['series'].min()} .. {df['series'].max()}")

    db = SessionLocal()
    try:
        payments = {p.tracking_code: p for p in db.query(Payment).filter(Payment.is_deleted == False).all()}  # noqa: E712
        employer_of_contract = dict(db.execute(text("select tracking_code, employer_code from contracts")).all())
        contracts = load_contracts(db)

        in_sheet_codes = set(df.loc[df["tracking_ok"], "pcode"])
        updates, undo = [], []
        new_rows, not_imported = [], []
        blank_matched = []

        def apply_fields(p: Payment, row, origin: str):
            """Refresh series / letter number / date on an existing payment; returns change dict or None."""
            changes = {}
            new_date = parse_date(row["letter_date"])
            if row["series"] and p.series != row["series"]:
                changes["series"] = (p.series, row["series"])
            if row["letter_no"] and p.notification_letter_number != row["letter_no"]:
                changes["notification_letter_number"] = (p.notification_letter_number, row["letter_no"])
            if new_date is not None and p.notification_date != new_date:
                changes["notification_date"] = (p.notification_date, new_date)
            if new_date is not None and (p.payment_date is None or p.payment_date == p.notification_date) and p.payment_date != new_date:
                changes["payment_date"] = (p.payment_date, new_date)
            if not changes:
                return None
            undo.append({"tracking_code": p.tracking_code, **{k: [str(v[0]) if v[0] is not None else None, str(v[1])] for k, v in changes.items()}})
            updates.append({"کد رهگیری پرداخت": p.tracking_code, "منشأ": origin, "سری (قبل)": changes.get("series", (p.series,))[0],
                            "سری (بعد)": changes.get("series", (None, p.series))[1],
                            "شماره نامه (قبل)": changes.get("notification_letter_number", (p.notification_letter_number,))[0],
                            "شماره نامه (بعد)": changes.get("notification_letter_number", (None, p.notification_letter_number))[1],
                            "تاریخ ابلاغ (قبل)": changes.get("notification_date", (p.notification_date,))[0],
                            "تاریخ ابلاغ (بعد)": changes.get("notification_date", (None, p.notification_date))[1],
                            "ستون‌های جابه‌جا در اکسل": "بله" if row["swapped"] else ""})
            if "series" in changes:
                p.series = row["series"]
            if "notification_letter_number" in changes:
                p.notification_letter_number = row["letter_no"]
            if "notification_date" in changes:
                p.notification_date = new_date
            if "payment_date" in changes:
                p.payment_date = new_date
            return changes

        for _, row in df.iterrows():
            code = row["pcode"] if row["tracking_ok"] else None

            if code is None:
                # blank / "محرمانه" tracking code: only recognise a DB payment that the sheet does not mention
                cands = [p for pc, p in payments.items()
                         if pc not in in_sheet_codes and p.series == row["series"]
                         and employer_of_contract.get(p.contract_tracking_code) == row["emp_code"]
                         and row["amount"] and float(p.amount) == float(row["amount"])]
                if len(cands) == 1:
                    blank_matched.append((cands[0].tracking_code, row["series"], row["amount"]))
                    apply_fields(cands[0], row, "کد رهگیری خالی در اکسل؛ تطبیق با سری+کارفرما+مبلغ")
                else:
                    not_imported.append({**row.to_dict(), "علت": "کد رهگیری پرداخت در اکسل خالی/«محرمانه» است -- ثبت دستی لازم است"})
                continue

            if code in payments:
                apply_fields(payments[code], row, "کد رهگیری")
                continue

            # missing from the DB -> find the contract
            contract_code, how, n = match_contract(row, contracts)
            if contract_code is None:
                not_imported.append({**row.to_dict(), "علت": how})
                continue
            letter_date = parse_date(row["letter_date"])
            new_rows.append({"payment": Payment(
                tracking_code=code, contract_tracking_code=contract_code, amount=int(float(row["amount"])),
                payment_date=letter_date, payment_year=PAYMENT_YEAR, funding_year=FUNDING_YEAR,
                series=row["series"], notification_letter_number=row["letter_no"], notification_date=letter_date,
                status="Final", is_deleted=False), "how": how, "row": row.to_dict()})

        # ------------------------------------------ effect on balances / contracts
        from services.financial_engine import calculate_combined_pool_balance, calculate_real_balance

        affected = sorted({employer_of_contract[n["payment"].contract_tracking_code] for n in new_rows})

        def snapshot():
            return {e: (calculate_real_balance(db, e, 1402), calculate_real_balance(db, e, 1404),
                        calculate_combined_pool_balance(db, e)) for e in affected}

        before = snapshot()
        db.add_all([n["payment"] for n in new_rows])
        db.flush()
        after = snapshot()
        names = dict(db.execute(text("select classification_code, name from employers")).all())
        newly_negative = []
        for e in affected:
            b, a = before[e], after[e]
            if any(a[i] < -0.5 <= b[i] for i in range(3)):
                newly_negative.append((e, names.get(e, ""), a))
        contract_paid = dict(db.execute(text(
            "select contract_tracking_code, sum(amount) from payments where is_deleted=false and status in ('Final','Draft') group by 1")).all())
        contract_total = dict(db.execute(text("select tracking_code, total_amount from contracts")).all())
        overpaid = sorted({(n["payment"].contract_tracking_code, int(contract_total[n["payment"].contract_tracking_code]),
                            int(contract_paid[n["payment"].contract_tracking_code]))
                           for n in new_rows
                           if contract_paid[n["payment"].contract_tracking_code] > contract_total[n["payment"].contract_tracking_code]})

        # --------------------------------------------------------- summary
        print(f"\nردیف‌های موجود که فیلدشان بروز می‌شود: {len(updates)}")
        c = Counter()
        for u in updates:
            if u["سری (قبل)"] != u["سری (بعد)"]: c["series"] += 1
            if u["شماره نامه (قبل)"] != u["شماره نامه (بعد)"]: c["letter number"] += 1
            if u["تاریخ ابلاغ (قبل)"] != u["تاریخ ابلاغ (بعد)"]: c["letter date"] += 1
        print("  به تفکیک فیلد:", dict(c))
        print("  تطبیق با کد رهگیری خالی:", blank_matched)
        total_new = sum(float(n["payment"].amount) for n in new_rows) / 1e6
        print(f"\nپرداخت‌های جدید قابل ثبت: {len(new_rows)} ردیف، {total_new:,.0f} میلیون ریال")
        by_series = Counter(n["payment"].series for n in new_rows)
        print("  به تفکیک سری:", dict(sorted(by_series.items(), key=lambda kv: series_key(kv[0]))))
        print("  روش تطبیق قرارداد:", dict(Counter(n["how"].split(" (")[0] for n in new_rows)))
        print(f"\nبدون ثبت (نیازمند بررسی): {len(not_imported)} ردیف")
        for r in not_imported:
            print(f"  {r['series']} | {r['pcode']} | {str(r['applicant'])[:40]} | {r['emp_code']} | {r['amount']} | {r['علت']}")

        print(f"\nکارفرمایانی که با این ثبت، مانده‌شان منفی می‌شود: {len(newly_negative)}")
        for e, nm, a in newly_negative:
            print(f"  {e} {nm[:40]}: ۱۴۰۲ {a[0]/1e6:,.0f} | ۱۴۰۴ {a[1]/1e6:,.0f} | تجمیعی {a[2]/1e6:,.0f} میلیون ریال")
        print(f"قراردادهایی که جمع پرداخت‌هایشان از مبلغ قرارداد بیشتر می‌شود: {len(overpaid)}")
        for code, total, paid in overpaid:
            print(f"  {code}: مبلغ قرارداد {total:,} | جمع پرداخت‌ها {paid:,}")

        # ---------------------------------------------------------- report
        def lines(new_filter):
            out = []
            for n in new_rows:
                if new_filter(n["payment"].series):
                    r = n["row"]
                    out.append({"سری": r["series"], "کد رهگیری پرداخت": r["pcode"], "کد رهگیری قرارداد (یافت‌شده)": n["payment"].contract_tracking_code,
                                "روش تطبیق": n["how"], "متقاضی": r["applicant"], "کد طبقه‌بندی": r["emp_code"], "دانشگاه": r["university"],
                                "فناور": r["researcher"], "عنوان قرارداد": r["title"], "مبلغ کل قرارداد (ریال)": r["contract_total"],
                                "مبلغ پرداخت (ریال)": int(float(r["amount"])), "شماره نامه ابلاغ": r["letter_no"], "تاریخ ابلاغ": r["letter_date"]})
            return pd.DataFrame(out)

        old_series = lambda s: series_key(s)[1] <= LAST_PREVIOUSLY_IMPORTED_SERIES  # noqa: E731
        sheets = {
            "ایمپورت‌نشده در سری‌های قبلی": lines(old_series),
            "ایمپورت جدید - سری ۲۶ تا ۳۰": lines(lambda s: not old_series(s)),
            "بدون قرارداد - نیازمند بررسی": pd.DataFrame([
                {"سری": r["series"], "کد رهگیری پرداخت": r["pcode"], "متقاضی": r["applicant"], "کد طبقه‌بندی": r["emp_code"],
                 "دانشگاه": r["university"], "فناور": r["researcher"], "عنوان قرارداد": r["title"],
                 "مبلغ کل قرارداد (ریال)": r["contract_total"], "مبلغ پرداخت (ریال)": r["amount"],
                 "شماره نامه ابلاغ": r["letter_no"], "تاریخ ابلاغ": r["letter_date"], "علت": r["علت"],
                 "سری جدید؟": "بله" if not old_series(r["series"]) else "خیر (سری قبلی)"} for r in not_imported]),
            "بروزرسانی ردیف‌های موجود": pd.DataFrame(updates),
        }

        if args.apply:
            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with pd.ExcelWriter(REPORT_PATH, engine="openpyxl") as writer:
                for name, frame in sheets.items():
                    frame.to_excel(writer, sheet_name=name[:31], index=False)
                    ws = writer.sheets[name[:31]]
                    ws.sheet_view.rightToLeft = True
                    ws.freeze_panes = "A2"
            UNDO_PATH.write_text(json.dumps({"updated": undo, "inserted": [n["payment"].tracking_code for n in new_rows]},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
            db.commit()
            print(f"\n✅ ثبت شد. گزارش: {REPORT_PATH}\n   لاگ بازگشت: {UNDO_PATH}")
        else:
            db.rollback()
            print("\n(dry run — چیزی نوشته نشد. برای ثبت --apply بدهید.)")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
