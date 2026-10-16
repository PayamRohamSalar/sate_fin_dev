"""Import the 1405 batch payments that never reached the database.

Background (2026-09-16)
-----------------------
Payam entered payment series 05-15..05-20 through the Streamlit batch-payment
form, but they are absent from ``payments`` -- no ``Draft`` rows, no
soft-deleted rows, and the API writes to this same ``sate_db``, so the records
simply never landed. The gap was caught while reconciling against the ATF
Fund's audit ledger: the Fund reported spending for بانک مرکزی (276000) that
our dashboard showed as zero.

The missing amounts reproduce the audit variances exactly, which is what
confirms this is a data gap rather than a formula bug:
  220360 پالایش و پخش   50,796M  (audit variance -50,796)
  292390 نفت‌خیز جنوب    40,500M  (audit variance -40,500)
  276000 بانک مرکزی      34,550M  (audit variance -34,550)

Source: ``جدول پرداخت 1405.xlsx`` (Payam's own export of the payment series),
which carries the payment tracking code, series, employer classification code,
contract title and total, the requested amount, and the notification letter
number/date -- but NOT the funding year.

Funding year
------------
The Excel has no funding-year column (in the form it is a per-row human
choice). Payam's instruction for this import: **every one of these rows is
funded from the 1404 pool**, so ``funding_year = 1404`` and
``payment_year = 1405`` throughout. This matters because "هزینه کرد سال مالی
1404" is defined by ``funding_year``, not the calendar disbursement year --
see ``scripts/reconcile_atf_audit.py``.

Contract resolution
-------------------
The Excel identifies the contract only indirectly, so contracts are matched on
(employer classification code + exact total contract amount), with the contract
title as the tie-breaker when an employer has several contracts of the same
value. Rows that resolve to no contract are NOT imported and are written to
``results/payments_1405_unmatched.xlsx`` for Payam to supply the contract data.

Usage
-----
    python scripts/import_payments_1405.py              # dry run, writes nothing
    python scripts/import_payments_1405.py --apply      # perform the insert
    python scripts/import_payments_1405.py --apply --fix-series

``--fix-series`` also relabels the 1405 payments that were entered with a bare
``21``..``25`` series (colliding with the 1403 series of the same name) to the
canonical ``05-21``..``05-25`` form. Amounts and every other field are left
untouched; only the label changes.

Re-running is safe: any tracking code already present is skipped.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal
from core.date_helper import parse_strict_jalali_date
from models.contract import Contract
from models.payment import Payment

SOURCE_FILE = Path(r"C:\Users\Payam\Downloads\جدول پرداخت 1405.xlsx")

# Known bad employer codes in the source Excel, confirmed against the main
# dashboard 2026-09-16: "موسسه تحقیقات سیاست علمی کشور_کارگزار..." carries
# "1400278579" in the "کد طبقه‌بندی" column, which matches no employer at
# all -- Payam found the real employer (with real contracts and credit
# transfers) live in the dashboard under classification_code 128342, and
# confirmed it's the same institution. Applied as a targeted correction
# rather than trusting the Excel's employer_code column for this applicant.
EMPLOYER_CODE_CORRECTIONS = {
    "1400278579": "128342",
}
UNMATCHED_PATH = Path(__file__).resolve().parents[1] / "results" / "payments_1405_unmatched.xlsx"

PAYMENT_YEAR = 1405
FUNDING_YEAR = 1404

COL_SERIES = "سری"
COL_TRACKING = "کد رهگیری"
COL_EMPLOYER_NAME = "متقاضی"
COL_EMPLOYER_CODE = "کد طبقه‌بندی"
COL_UNIVERSITY = "دانشگاه"
COL_RESEARCHER = "فناور"
COL_TITLE = "عنوان قرارداد"
COL_CONTRACT_TOTAL = "مبلغ کل قرارداد(ریال)"
COL_AMOUNT = "مبلغ درخواستی(ریال)"
COL_LETTER_NO = "شماره نامه ابلاغ"
COL_LETTER_DATE = "تاریخ ابلاغ"


def normalize(text) -> str:
    """Collapse whitespace and unify Arabic/Persian letter variants."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    cleaned = str(text).replace("\u200c", " ").replace("ي", "ی").replace("ك", "ک")
    return " ".join(cleaned.split())


def parse_letter_date(value):
    """Parse the Jalali notification date, tolerating the malformed entries.

    A few rows carry a letter *number* (e.g. ``3/12/05637``) in the date
    column; those are left as ``None`` rather than guessed at.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    try:
        return parse_strict_jalali_date(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_missing_rows(db) -> pd.DataFrame:
    """Read the Excel and keep only rows whose tracking code is absent."""
    existing = {code for (code,) in db.query(Payment.tracking_code).all()}
    df = pd.read_excel(SOURCE_FILE, sheet_name="Sheet1")
    df["tracking_code"] = df[COL_TRACKING].astype(str).str.strip()
    df["employer_code"] = df[COL_EMPLOYER_CODE].astype(str).str.strip()
    df["employer_code"] = df["employer_code"].replace(EMPLOYER_CODE_CORRECTIONS)
    df["amount"] = pd.to_numeric(df[COL_AMOUNT], errors="coerce")
    df["contract_total"] = pd.to_numeric(df[COL_CONTRACT_TOTAL], errors="coerce")
    return df[~df["tracking_code"].isin(existing)].copy()


def build_contract_index(db) -> dict:
    """(employer_code, total_amount) -> list of candidate contracts."""
    index: dict[tuple[str, float], list[Contract]] = {}
    contracts = db.query(Contract).filter(Contract.is_deleted == False).all()  # noqa: E712
    for contract in contracts:
        if contract.total_amount is None:
            continue
        key = (str(contract.employer_code).strip(), float(contract.total_amount))
        index.setdefault(key, []).append(contract)
    return index


def resolve_contract(row, index) -> tuple[str | None, str]:
    """Return (contract_tracking_code, reason) for one payment row."""
    if pd.isna(row["contract_total"]):
        return None, "مبلغ کل قرارداد عددی نیست (محرمانه)"

    candidates = index.get((row["employer_code"], float(row["contract_total"])), [])
    if not candidates:
        return None, "قراردادی با این کد مشمول و مبلغ کل در دیتابیس نیست"
    if len(candidates) == 1:
        return candidates[0].tracking_code, "مبلغ کل + کد مشمول"

    title = normalize(row[COL_TITLE])
    exact = [c for c in candidates if normalize(c.title) == title]
    if len(exact) == 1:
        return exact[0].tracking_code, "مبلغ کل + کد مشمول + عنوان"
    return None, f"{len(candidates)} قرارداد هم‌مبلغ و عنوان تفکیک‌کننده نبود"


def fix_series_labels(db, *, apply: bool) -> int:
    """Relabel bare 1405 series ``21``..``25`` to canonical ``05-NN``."""
    rows = (
        db.query(Payment)
        .filter(
            Payment.payment_year == PAYMENT_YEAR,
            Payment.series.in_([str(n) for n in range(1, 60)]),
            Payment.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    for payment in rows:
        new_label = f"05-{int(payment.series):02d}"
        print(f"  {payment.tracking_code}: series {payment.series!r} -> {new_label!r}")
        if apply:
            payment.series = new_label
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write to the database")
    parser.add_argument("--fix-series", action="store_true", help="also relabel bare 1405 series")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        missing = load_missing_rows(db)
        index = build_contract_index(db)

        to_insert, unmatched = [], []
        for _, row in missing.iterrows():
            # Guard against a real bug found 2026-09-16: a blank "کد رهگیری"
            # cell survives ``.astype(str).str.strip()`` as an actual Python
            # float NaN (pandas' "str" extension dtype keeps missing values
            # as NA rather than the literal text "nan"). Binding that NaN as
            # the primary key doesn't error -- psycopg2 silently adapts it to
            # the 3-character text 'NaN', which can collide with (or create)
            # a bogus 'NaN' row. This bit a real import: a row for a
            # confidential Bushehr-plant contract with no tracking code
            # resolved fine by employer+amount and got inserted as pk='NaN',
            # duplicating a pre-existing legitimate payment ('C_2273', same
            # contract, same amount) that the case-sensitive lookup missed.
            # Caught only by noticing the aggregate total didn't add up;
            # the duplicate was soft-deleted by hand. Any row with no real
            # tracking code must be reported for manual entry, never
            # auto-resolved and inserted.
            if pd.isna(row["tracking_code"]):
                unmatched.append({
                    "سری": row[COL_SERIES],
                    "کد رهگیری پرداخت": None,
                    "متقاضی": row[COL_EMPLOYER_NAME],
                    "کد طبقه‌بندی": row["employer_code"],
                    "دانشگاه": row[COL_UNIVERSITY],
                    "فناور": row[COL_RESEARCHER],
                    "عنوان قرارداد": row[COL_TITLE],
                    "مبلغ کل قرارداد (ریال)": row[COL_CONTRACT_TOTAL],
                    "مبلغ پرداختی (ریال)": row[COL_AMOUNT],
                    "شماره نامه ابلاغ": row[COL_LETTER_NO],
                    "تاریخ ابلاغ": row[COL_LETTER_DATE],
                    "علت عدم ثبت": "ستون «کد رهگیری» در اکسل خالی است -- نیازمند ثبت دستی",
                })
                continue

            contract_code, reason = resolve_contract(row, index)
            if contract_code is None:
                unmatched.append({
                    "سری": row[COL_SERIES],
                    "کد رهگیری پرداخت": row["tracking_code"],
                    "متقاضی": row[COL_EMPLOYER_NAME],
                    "کد طبقه‌بندی": row["employer_code"],
                    "دانشگاه": row[COL_UNIVERSITY],
                    "فناور": row[COL_RESEARCHER],
                    "عنوان قرارداد": row[COL_TITLE],
                    "مبلغ کل قرارداد (ریال)": row[COL_CONTRACT_TOTAL],
                    "مبلغ پرداختی (ریال)": row[COL_AMOUNT],
                    "شماره نامه ابلاغ": row[COL_LETTER_NO],
                    "تاریخ ابلاغ": row[COL_LETTER_DATE],
                    "علت عدم ثبت": reason,
                })
                continue

            letter_date = parse_letter_date(row[COL_LETTER_DATE])
            to_insert.append(Payment(
                tracking_code=row["tracking_code"],
                contract_tracking_code=contract_code,
                amount=row["amount"],
                payment_date=letter_date,
                payment_year=PAYMENT_YEAR,
                funding_year=FUNDING_YEAR,
                series=str(row[COL_SERIES]).strip(),
                notification_letter_number=(
                    None if pd.isna(row[COL_LETTER_NO]) else str(row[COL_LETTER_NO]).strip()
                ),
                notification_date=letter_date,
                status="Final",
                is_deleted=False,
            ))

        total_new = sum(float(p.amount) for p in to_insert) / 1_000_000
        print(f"ردیف‌های غایب در اکسل: {len(missing)}")
        print(f"قابل ثبت: {len(to_insert)} ردیف، {total_new:,.0f} میلیون ریال")
        print(f"بدون قرارداد متناظر: {len(unmatched)} ردیف")

        by_series = {}
        for payment in to_insert:
            by_series[payment.series] = by_series.get(payment.series, 0) + 1
        print("به تفکیک سری:", dict(sorted(by_series.items())))

        if unmatched:
            UNMATCHED_PATH.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(unmatched).to_excel(UNMATCHED_PATH, index=False)
            print(f"فهرست ردیف‌های بدون قرارداد: {UNMATCHED_PATH}")

        if args.fix_series:
            print("\n--- اصلاح برچسب سری ---")
            print(f"تعداد: {fix_series_labels(db, apply=args.apply)}")

        if args.apply:
            db.add_all(to_insert)
            db.commit()
            print(f"\n✅ {len(to_insert)} پرداخت ثبت شد.")
        else:
            db.rollback()
            print("\n(dry run — چیزی در دیتابیس نوشته نشد. برای ثبت --apply بدهید.)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
