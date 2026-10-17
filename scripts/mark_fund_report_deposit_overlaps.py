"""Mark 1405 deposits that the Fund report already contained (2026-10-16).

On 2026-10-16 Payam sent the list of 1405 deposits to date (ماده 65 ضوابط
اجرایی قانون بودجه ۱۴۰۵) and we entered the missing ones as new
``deposit_receipts``. The Fund report (valid through 1405/06/22) had already
counted some of them, but ``services/fund_report.py`` adds every receipt newer
than the snapshot's baseline to the Fund side -- so those were counted twice
there. This script records, per receipt, the part the snapshot already holds
(``fund_report_deposit_overlaps``); the Fund side then subtracts it.

Only the employers where the evidence is unambiguous are marked: the Fund's
«واریزی 1404 به بعد» minus our own pre-baseline 1404/1405 deposits is at least
the whole new receipt. Employers where the Fund holds only part of the receipt
(210000, 292400, 214500) are left out until Payam confirms.

Idempotent: re-running does not duplicate rows. Dry-run by default.

Usage:
    python scripts/mark_fund_report_deposit_overlaps.py            # dry-run
    python scripts/mark_fund_report_deposit_overlaps.py --commit
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal, engine  # noqa: E402
import models.contract, models.transfer  # noqa: E402,F401  (mapper registry)
from models.deposits import DepositReceipt  # noqa: E402
from models.fund_report import FundReportDepositOverlap  # noqa: E402
from services.fund_report import get_latest_snapshot  # noqa: E402

DEPOSIT_YEAR = 1405
# employer code of the deposit receipt -> the whole receipt is already in the Fund report
FULLY_IN_FUND_REPORT = ["200505", "254000", "290710", "292750", "278500", "216000"]
NOTE = "واریزی ۱۴۰۵ ثبت‌شده در ۱۴۰۵/۰۷/۲۴ که گزارش صندوق (تا ۱۴۰۵/۰۶/۲۲) از قبل لحاظ کرده بود"


def main() -> int:
    commit = "--commit" in sys.argv
    FundReportDepositOverlap.__table__.create(bind=engine, checkfirst=True)

    db = SessionLocal()
    try:
        snapshot = get_latest_snapshot(db)
        if snapshot is None:
            print("No Fund snapshot found.")
            return 1
        print(f"Snapshot #{snapshot.id}, baseline deposit receipt id {snapshot.baseline_deposit_receipt_id}")

        for code in FULLY_IN_FUND_REPORT:
            receipts = (
                db.query(DepositReceipt)
                .filter(
                    DepositReceipt.employer_code == code,
                    DepositReceipt.fiscal_year == DEPOSIT_YEAR,
                    DepositReceipt.is_deleted == False,  # noqa: E712
                    DepositReceipt.id > snapshot.baseline_deposit_receipt_id,
                )
                .all()
            )
            if len(receipts) != 1:
                print(f"{code}: expected exactly one post-baseline 1405 receipt, found {len(receipts)} -- skipped")
                return 1
            receipt = receipts[0]
            exists = (
                db.query(FundReportDepositOverlap)
                .filter(
                    FundReportDepositOverlap.snapshot_id == snapshot.id,
                    FundReportDepositOverlap.deposit_receipt_id == receipt.id,
                    FundReportDepositOverlap.is_deleted == False,  # noqa: E712
                )
                .count()
            )
            if exists:
                print(f"{code}: receipt #{receipt.id} already marked")
                continue
            db.add(FundReportDepositOverlap(
                snapshot_id=snapshot.id, deposit_receipt_id=receipt.id,
                amount=int(receipt.deposit_amount), note=NOTE,
            ))
            print(f"{code}: receipt #{receipt.id} marked, {int(receipt.deposit_amount):,} Rial already in the Fund report")

        if commit:
            db.commit()
            print("COMMITTED")
        else:
            db.rollback()
            print("dry-run, rolled back")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
