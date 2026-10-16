"""One-off import of the Fund's financial-status report (Sandogh_Report.xlsx).

Columns of the Fund's file (matched to employers by «شماره طبقه بندی», never
by name -- names differ):

    شرکت | شماره طبقه بندی | دستگاه اجرایی مرتبط | اعتبار 1402-1403 |
    واریزی 1404 تا 14050622 | پرداختی حواله 1404 و 1405 |
    کارمزد صندوق مطابق مصوبه هیات امنا | مانده اعتبار

Facts verified on the file (2026-10-13):
* مانده = اعتبار 1402-1403 + واریزی 1404 - پرداختی   (کارمزد کسر نمی‌شود)
  -- true on all 156 rows that carry a numeric balance.
* 103 rows have an empty / text («چینی فروشان») balance cell: their balance
  is recomputed with the same formula; the raw cell is kept in
  ``reported_balance`` / ``note``.
* 2 rows carry the text «تجمیع با نفت مناطق مرکزی» instead of a number in the
  1402-1403 column: stored as 0 with the text in ``note``.

The snapshot is idempotent per ``--label``: run again with ``--replace`` to
reload it.

Usage
-----
    python scripts/import_fund_report.py "C:\\Users\\Payam\\Desktop\\Sandogh_Report.xlsx"
    python scripts/import_fund_report.py <file> --replace
    python scripts/import_fund_report.py <file> --dry-run
"""

from __future__ import annotations

import argparse
import io
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import func

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import Base, SessionLocal, engine  # noqa: E402
import models.contract, models.transfer  # noqa: E402,F401  (mapper registry)
from models.deposits import DepositReceipt  # noqa: E402
from models.employer import Employer  # noqa: E402
from models.fund_report import FundReportLine, FundReportSnapshot  # noqa: E402

DEFAULT_LABEL = "گزارش صندوق عتف - تا پایان سری پرداخت 25"
DEFAULT_CUTOFF_NOTE = "پرداخت‌ها تا پایان سری 25؛ واریزی‌ها تا 1405/06/22"
DEFAULT_SERIES = "05-25"

# positional (header text is not trusted: it contains stray spaces)
COLS = ["name", "code", "agency", "credit", "deposit", "paid", "fee", "balance"]


def to_number(value):
    """(number, note): text cells become (None, text)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None, None
    try:
        return Decimal(str(value)), None
    except Exception:
        return None, str(value).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("excel", type=Path)
    parser.add_argument("--label", default=DEFAULT_LABEL)
    parser.add_argument("--cutoff-note", default=DEFAULT_CUTOFF_NOTE)
    parser.add_argument("--series", default=DEFAULT_SERIES, help="last payment series included in the report")
    parser.add_argument("--replace", action="store_true", help="reload if this label already exists")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    df = pd.read_excel(args.excel, sheet_name=0, header=0)
    df = df.iloc[:, : len(COLS)]
    df.columns = COLS
    print(f"خوانده شد: {len(df)} ردیف از {args.excel.name}")

    Base.metadata.create_all(bind=engine, tables=[FundReportSnapshot.__table__, FundReportLine.__table__])

    db = SessionLocal()
    try:
        existing_codes = {c for (c,) in db.query(Employer.classification_code).filter(Employer.is_deleted == False)}  # noqa: E712
        snapshot = db.query(FundReportSnapshot).filter(FundReportSnapshot.label == args.label).first()
        if snapshot is not None:
            if not args.replace:
                print(f"گزارش «{args.label}» قبلاً ثبت شده است. برای بارگذاری مجدد --replace بزنید.")
                return 1
            db.query(FundReportLine).filter(FundReportLine.snapshot_id == snapshot.id).delete()
            db.delete(snapshot)
            db.flush()

        baseline_id = db.query(func.max(DepositReceipt.id)).scalar() or 0
        snapshot = FundReportSnapshot(
            label=args.label,
            source_file=args.excel.name,
            cutoff_note=args.cutoff_note,
            baseline_payment_series=args.series,
            baseline_deposit_receipt_id=int(baseline_id),
            is_deleted=False,
        )
        db.add(snapshot)
        db.flush()

        seen: set[str] = set()
        problems: list[str] = []
        recomputed = 0
        for pos, row in df.iterrows():
            code = str(row["code"]).strip()
            if code.endswith(".0"):
                code = code[:-2]
            if not code.isdigit():
                problems.append(f"ردیف {pos + 2}: شماره طبقه بندی نامعتبر ({row['code']!r})")
                continue
            if code not in existing_codes:
                problems.append(f"ردیف {pos + 2}: کد {code} ({row['name']}) در جدول کارفرمایان نیست")
                continue
            if code in seen:
                problems.append(f"ردیف {pos + 2}: کد {code} تکراری است")
                continue
            seen.add(code)

            notes = []
            credit, n = to_number(row["credit"])
            if n:
                notes.append(f"اعتبار 1402-1403: {n}")
            deposit, n = to_number(row["deposit"])
            if n:
                notes.append(f"واریزی: {n}")
            paid, n = to_number(row["paid"])
            if n:
                notes.append(f"پرداختی: {n}")
            fee, n = to_number(row["fee"])
            if n:
                notes.append(f"کارمزد: {n}")
            reported, n = to_number(row["balance"])
            if n:
                notes.append(f"مانده: {n}")

            credit, deposit, paid, fee = (x or Decimal(0) for x in (credit, deposit, paid, fee))
            balance = credit + deposit - paid
            if reported is None:
                recomputed += 1
            elif abs(reported - balance) > 1:
                problems.append(
                    f"کد {code}: مانده گزارش ({reported:,.0f}) با فرمول ({balance:,.0f}) نمی‌خواند؛ فرمول استفاده شد"
                )

            db.add(FundReportLine(
                snapshot_id=snapshot.id,
                employer_code=code,
                company_name_in_report=str(row["name"]).strip() if pd.notna(row["name"]) else None,
                executive_agency=str(row["agency"]).strip() if pd.notna(row["agency"]) else None,
                credit_1402_1403=credit,
                deposit_1404=deposit,
                paid_1404_1405=paid,
                fund_fee=fee,
                reported_balance=reported,
                balance=balance,
                note=" | ".join(notes) or None,
                is_deleted=False,
            ))
        db.flush()

        total = db.query(
            func.count(FundReportLine.id), func.sum(FundReportLine.credit_1402_1403),
            func.sum(FundReportLine.deposit_1404), func.sum(FundReportLine.paid_1404_1405),
            func.sum(FundReportLine.fund_fee), func.sum(FundReportLine.balance),
        ).filter(FundReportLine.snapshot_id == snapshot.id).one()

        print("=" * 70)
        print(f"ردیف ثبت‌شده: {total[0]}  |  مانده بازمحاسبه‌شده (خالی در فایل): {recomputed}")
        print(f"اعتبار ۱۴۰۲-۱۴۰۳: {float(total[1])/1e6:,.0f}  | واریزی ۱۴۰۴: {float(total[2])/1e6:,.0f}"
              f"  | پرداختی: {float(total[3])/1e6:,.0f}  | کارمزد: {float(total[4])/1e6:,.0f}"
              f"  | مانده: {float(total[5])/1e6:,.0f}   (میلیون ریال)")
        print(f"مبنای به‌روزرسانی موازی: سری پرداخت بعد از {args.series}، "
              f"deposit_receipts.id > {int(baseline_id)}")
        for p in problems:
            print("  [!]", p)

        if args.dry_run:
            db.rollback()
            print("(dry-run: چیزی ذخیره نشد)")
        else:
            db.commit()
            print("ذخیره شد.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
