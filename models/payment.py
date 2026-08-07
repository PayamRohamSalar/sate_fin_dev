"""Payment (پرداختی‌ها) model for the SATE financial system.

Records individual disbursements made against a research contract. Each payment
references its parent contract via ``contract_tracking_code`` and captures the
amount, date, execution year and payment type.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String

from core.database import Base, SoftDeleteMixin


class Payment(SoftDeleteMixin, Base):
    """A single payment made against a research contract.

    Attributes
    ----------
    tracking_code : str
        Unique tracking code for the payment; primary key (max 50 chars).
    contract_tracking_code : str
        Foreign key to ``contracts.tracking_code``.
    amount : Decimal
        Payment amount (Numeric(18, 2)).
    payment_date : date
        Date the payment was executed.
    execution_year : int
        Fiscal (execution) year the payment is recorded against.
    payment_type : str
        Category/type of the payment (max 50 chars).
    series : str or None
        Optional series/sequence identifier.
    notification_letter_number : str or None
        Optional notification letter reference number.
    notification_date : date or None
        Optional date of the notification letter.
    payment_year : int or None
        Cash-flow year of the payment (legacy/compatibility field).
    funding_year : int or None
        Budget-consumption year of the payment (legacy/compatibility field).
    attachment_path : str or None
        Optional path to a supporting attachment.
    status : str
        Lifecycle status; ``"Draft"`` while staged in the batch-payment
        cart (reserves funds against the employer's balance without being
        a finalized disbursement) or ``"Final"`` once confirmed. Defaults
        to ``"Final"`` so directly-inserted payments (e.g. bulk ETL
        imports) behave as before this field existed.
    """

    __tablename__ = "payments"

    tracking_code = Column(String(50), primary_key=True)
    contract_tracking_code = Column(
        String(50),
        ForeignKey("contracts.tracking_code"),
        nullable=False,
    )
    amount = Column(Numeric(18, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    execution_year = Column(Integer, nullable=False)
    payment_type = Column(String(50), nullable=False)

    series = Column(String(50), nullable=True)
    notification_letter_number = Column(String(100), nullable=True)
    notification_date = Column(Date, nullable=True)
    payment_year = Column(Integer, nullable=True)
    funding_year = Column(Integer, nullable=True)
    attachment_path = Column(String(255), nullable=True)
    status = Column(String(20), default="Final")

    def __repr__(self):
        return (
            f"<Payment(tracking_code={self.tracking_code!r}, "
            f"contract={self.contract_tracking_code!r}, amount={self.amount})>"
        )
