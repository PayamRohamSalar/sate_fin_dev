"""Correct DepositReceipt.deposit_amount for fiscal_year=1402 against the
Fund's authoritative per-employer deposit list.

Background (2026-09-16): Payam caught a large error in our 1402 deposit for
"شرکت انتقال گاز ایران" (292910) -- our DB had 194,755,000,000 Rial, the
Fund's own file (``واریزی 1402 مشمولین.xlsx``) says 71,700,000,000. He asked
to re-sync ALL of 1402 from this file, since other employers may have the
same error.

Source file structure: one row per employer (399 rows incl. a "جمع کل" grand
total row), columns "شماره طبقه‌بندی" / "نام شرکت" / "پرداخت سال جاری"
(=the 1402 deposit). 7 "سازمان منطقه آزاد ..." (Free Zone) rows have a blank
code and blank amount -- skipped, nothing to resolve them to.

DB has exactly one DepositReceipt row per (employer_code, fiscal_year=1402)
today (245 employers, verified 1:1 before running this) -- so this is a
straight update-in-place for matched employers, an insert for a fund-listed
employer missing an existing 1402 row, and a flagged (not touched) list for
DB employers with a 1402 row that the fund's file doesn't mention at all.

Usage: python scripts/fix_deposits_1402.py [--apply]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal
from models.deposits import DepositReceipt
from models.employer import Employer

SOURCE_FILE = Path(r"C:\Users\Payam\Downloads\تطبیق حسابرسی\واریزی 1402 مشمولین.xlsx")
FISCAL_YEAR = 1402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    df = pd.read_excel(SOURCE_FILE, sheet_name="Sheet1")
    df["code"] = df["شماره طبقه بندی"].astype(str).str.strip()
    df = df[(df["code"] != "جمع کل") & df["code"].notna() & (df["code"] != "nan")]
    df["amount"] = pd.to_numeric(df["پرداخت سال جاری"], errors="coerce")
    df = df[df["amount"].notna()]

    db = SessionLocal()
    try:
        valid_codes = {c for (c,) in db.query(Employer.classification_code).all()}
        existing = {
            r.employer_code: r
            for r in db.query(DepositReceipt).filter(
                DepositReceipt.fiscal_year == FISCAL_YEAR, DepositReceipt.is_deleted == False  # noqa: E712
            ).all()
        }

        updated, inserted, unknown_employer = [], [], []
        for _, row in df.iterrows():
            code, name, amount = row["code"], row["نام شرکت"], float(row["amount"])
            if code not in valid_codes:
                unknown_employer.append((code, name, amount))
                continue
            if code in existing:
                rec = existing[code]
                if float(rec.deposit_amount) != amount:
                    updated.append((code, name, float(rec.deposit_amount), amount))
                    rec.deposit_amount = amount
            else:
                inserted.append((code, name, amount))
                db.add(DepositReceipt(
                    employer_code=code, fiscal_year=FISCAL_YEAR, deposit_amount=amount,
                    deposit_date=None, receipt_number=None, is_deleted=False,
                ))

        file_codes = set(df["code"])
        missing_from_file = sorted(set(existing) - file_codes)

        print(f"تغییریافته: {len(updated)} | جدید: {len(inserted)} | کد ناشناس در دیتابیس: {len(unknown_employer)}")
        if updated:
            print("\n-- بزرگ‌ترین تغییرها (اختلاف نسبی) --")
            for code, name, old, new in sorted(updated, key=lambda t: abs(t[3] - t[2]), reverse=True)[:15]:
                print(f"  {code} {name}: {old:,.0f} -> {new:,.0f}  (Δ={new - old:,.0f})")
        if unknown_employer:
            print("\n-- کد در فایل صندوق هست ولی در جدول employers نیست --")
            for code, name, amount in unknown_employer:
                print(f"  {code} {name}: {amount:,.0f}")
        if missing_from_file:
            print(f"\n-- {len(missing_from_file)} مشمول دارای رکورد 1402 در دیتابیس که در این فایل نیامده‌اند (دست‌نخورده ماندند) --")
            for code in missing_from_file:
                print(f"  {code}: {float(existing[code].deposit_amount):,.0f}")

        if args.apply:
            db.commit()
            print("\n✅ اعمال شد.")
        else:
            db.rollback()
            print("\n(dry run -- چیزی ذخیره نشد. برای اعمال --apply بدهید.)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
