"""Trustee/custodial payment ("پرداخت‌های امانی") model for the SATE financial system.

A trustee payment is a disbursement toward a research contract that was paid
directly by the executing university/institution out of its own funds,
entirely outside the employer-managed budget pool that
``services.financial_engine.calculate_real_balance`` tracks. These rows are
recorded purely for contract-status reconciliation (e.g. explaining a
"stagnant" contract that otherwise looks unpaid) and must never be joined
into, or summed alongside, the ``payments`` table when computing an
employer's real balance or any other credit/budget figure.

``contract_tracking_code`` is intentionally a plain string, not a foreign
key: the source data (an external reconciliation spreadsheet) is not
guaranteed to reference a contract that exists in ``contracts``, and a
strict FK would make otherwise-valid rows unimportable.
"""

from sqlalchemy import Column, Date, Integer, Numeric, String, Text

from core.database import Base, SoftDeleteMixin


class TrusteePayment(SoftDeleteMixin, Base):
    """A payment funded by the executing institution, outside SATE's budget pool.

    Attributes
    ----------
    id : int
        Auto-incrementing surrogate primary key.
    tracking_code : str
        The payment's own tracking code from the source reconciliation file;
        unique, but not a foreign key into ``payments`` (it explicitly does
        not exist there).
    contract_tracking_code : str or None
        The contract this payment was made against, as a plain reference
        (not a foreign key — see module docstring).
    employer_code : str or None
        The contract's employer, resolved at import time for informational/
        reporting purposes only. Never used in balance calculations.
    amount : Decimal
        Payment amount in Rials, as reported by the source file.
    payment_year : int or None
        Fiscal year the payment was recorded against in the source file.
    notification_letter_number : str or None
        Reference number of the notification letter, when available.
    notification_date : date or None
        Date of the notification letter, when available.
    source_note : str or None
        Free-text note documenting where this record came from.
    """

    __tablename__ = "trustee_payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_code = Column(String(50), nullable=False, unique=True, index=True)
    contract_tracking_code = Column(String(50), nullable=True, index=True)
    employer_code = Column(String(20), nullable=True, index=True)
    amount = Column(Numeric(22, 0), nullable=False)
    payment_year = Column(Integer, nullable=True)
    notification_letter_number = Column(String(100), nullable=True)
    notification_date = Column(Date, nullable=True)
    source_note = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<TrusteePayment(tracking_code={self.tracking_code!r}, "
            f"contract={self.contract_tracking_code!r}, amount={self.amount})>"
        )
