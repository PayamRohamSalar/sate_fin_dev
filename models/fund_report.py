"""Fund (صندوق عتف) financial-status report snapshots.

One-off import of the Fund's «گزارش وضعیت مالی مشمولین» (Sandogh_Report.xlsx,
received 2026-10-13, valid through payment series 05-25). It is kept in its
own tables -- never mixed with our deposit/payment rows -- so the dashboard
can show OUR figures next to THE FUND's figures.

The snapshot is static; to keep the Fund side moving in parallel with our
own data entry, ``services/fund_report.py`` adds what we entered AFTER the
snapshot (deposit receipts with ``id > baseline_deposit_receipt_id`` and
payments in a series after ``baseline_payment_series``).
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)

from core.database import Base, SoftDeleteMixin


class FundReportSnapshot(SoftDeleteMixin, Base):
    """Header of one imported Fund report."""

    __tablename__ = "fund_report_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(200), nullable=False, unique=True, comment="عنوان گزارش")
    source_file = Column(String(255), nullable=True)
    cutoff_note = Column(String(300), nullable=True, comment="مقطع گزارش (متن)")
    baseline_payment_series = Column(
        String(20), nullable=False, comment="آخرین سری پرداخت لحاظ‌شده در گزارش، مثل 05-25"
    )
    baseline_deposit_receipt_id = Column(
        Integer, nullable=False,
        comment="بزرگ‌ترین deposit_receipts.id هنگام ثبت؛ واریزی‌های بعدی به موازات اضافه می‌شود",
    )
    created_at = Column(DateTime, server_default=func.now())


class FundReportDepositOverlap(SoftDeleteMixin, Base):
    """Part of one of OUR deposit receipts that the Fund snapshot already contains.

    ``services/fund_report.py`` adds every deposit receipt with
    ``id > baseline_deposit_receipt_id`` to the Fund side to keep it moving in
    parallel with our data entry. That is wrong for a receipt we entered after
    the baseline but that the Fund had already counted (e.g. the 1405 deposits
    entered on 2026-10-16 from Payam's list, many of which were inside the
    Fund's report dated 1405/06/22). Such a receipt gets a row here, and its
    ``amount`` is subtracted from the parallel update so it is not counted
    twice on the Fund side. ``amount`` may be less than the receipt's amount
    when the snapshot only holds part of it.
    """

    __tablename__ = "fund_report_deposit_overlaps"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "deposit_receipt_id", name="uq_fund_overlap_snapshot_receipt"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(
        Integer, ForeignKey("fund_report_snapshots.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    deposit_receipt_id = Column(
        Integer, ForeignKey("deposit_receipts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount = Column(
        Numeric(22, 0), nullable=False,
        comment="بخشی از این واریزی (ریال) که گزارش صندوق از قبل لحاظ کرده است",
    )
    note = Column(Text, nullable=True)


class FundReportLine(SoftDeleteMixin, Base):
    """One row of the Fund report (one employer, as listed by the Fund)."""

    __tablename__ = "fund_report_lines"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "employer_code", name="uq_fund_line_snapshot_employer"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(
        Integer, ForeignKey("fund_report_snapshots.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    employer_code = Column(
        String(20), ForeignKey("employers.classification_code"), nullable=False, index=True,
        comment="شماره طبقه بندی",
    )
    company_name_in_report = Column(String(300), nullable=True, comment="شرکت (به‌نام گزارش صندوق)")
    executive_agency = Column(String(100), nullable=True, comment="دستگاه اجرایی مرتبط")

    credit_1402_1403 = Column(Numeric(22, 2), nullable=False, default=0, comment="اعتبار 1402-1403")
    deposit_1404 = Column(Numeric(22, 2), nullable=False, default=0, comment="واریزی 1404 تا 1405/06/22")
    paid_1404_1405 = Column(Numeric(22, 2), nullable=False, default=0, comment="پرداختی حواله 1404 و 1405")
    fund_fee = Column(Numeric(22, 2), nullable=False, default=0, comment="کارمزد صندوق (از مانده کسر نمی‌شود)")
    reported_balance = Column(Numeric(22, 2), nullable=True, comment="مانده اعتبار طبق ستون گزارش (ممکن است خالی باشد)")
    balance = Column(
        Numeric(22, 2), nullable=False, default=0,
        comment="مانده = اعتبار 1402-1403 + واریزی 1404 - پرداختی (کارمزد کسر نمی‌شود)",
    )
    note = Column(Text, nullable=True, comment="توضیح متنی داخل فایل صندوق (مثلاً تجمیع با ...)")

    def __repr__(self):
        return f"<FundReportLine(snapshot={self.snapshot_id}, employer={self.employer_code}, balance={self.balance})>"
