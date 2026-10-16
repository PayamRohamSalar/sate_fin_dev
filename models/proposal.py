"""Proposal (پیشنهاده) model for the SATE financial system.

A proposal is a university/researcher's response to a posted ``Demand``.
It is the missing link between the demand side (who asked for what) and
the contract side (what was actually signed): ``Contract.proposal_id``
already stores the winning proposal's ``Proposal.id`` for contracts where
that link is known (see that column's notes on the ~40% of contracts where
it instead defaults to the contract's own tracking_code -- a pre-existing
placeholder, not a real link, from before this table existed).

Sourced from a raw view export of the system's proposal registry
(``vw_proposals.csv``); trimmed to only the fields needed for the intended
analyses (which demand got how many proposals, who submitted them, their
approval status, and the eventual contract link) -- the view carries other
columns (abstract, proposed cost/duration, etc.) that were deliberately
left out as unneeded for now.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, and_, cast
from sqlalchemy.orm import foreign, relationship

from core.database import Base, SoftDeleteMixin
from models.contract import Contract


class Proposal(SoftDeleteMixin, Base):
    """One proposal submitted by a researcher/university against a demand.

    Attributes
    ----------
    id : int
        Proposal ID as assigned by the SATE system; primary key (not
        autoincrement -- taken verbatim from the source export so it stays
        the same value ``Contract.proposal_id`` refers to).
    demand_tracking_code : str or None
        Tracking code of the ``Demand`` this proposal responds to, resolved
        from the source view's internal request ID. Informational only
        (not an enforced foreign key): a small fraction of proposals
        reference a request ID absent from the demand export snapshot.
    researcher_name : str
        Name of the submitting researcher exactly as exported
        ("lk_Contractor"). Free text -- see ``researcher_code``.
    researcher_code : str or None
        National code of the matching ``Researcher``, resolved by exact
        name match. Informational only, same caveat as ``employer_code``
        on :class:`~models.demand.Demand`.
    university_name : str or None
        Name of the submitting university/institute ("lk_UniversityTitle").
    university_id : str or None
        National ID of the matching ``University``, resolved by exact name
        match. Informational only, same caveat as above.
    status_code : int or None
        Numeric proposal status as exported ("lk_StatusID").
    status_title : str or None
        Persian label of the proposal status ("lk_StatusTitle") -- one of
        "ذخیره موقت", "در انتظار تایید متقاضی",
        "در انتظار تایید موسسه / دانشگاه", "تایید نهایی", "رد".
    submitted_at : datetime or None
        Timestamp the proposal was submitted ("CreateDate").
    """

    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, autoincrement=False)
    demand_tracking_code = Column(String(20), nullable=True, index=True)
    researcher_name = Column(String(200), nullable=False)
    researcher_code = Column(String(10), nullable=True, index=True)
    university_name = Column(String(300), nullable=True)
    university_id = Column(String(20), nullable=True, index=True)
    status_code = Column(Integer, nullable=True)
    status_title = Column(String(50), nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    # Convenience read-only accessor for "did this proposal become a
    # contract" -- backed by Contract.proposal_id, which is not a declared
    # ForeignKey (see that column's comment in models/contract.py for why,
    # and for the placeholder rows this join deliberately excludes).
    # viewonly=True because the link isn't a real FK: SQLAlchemy must never
    # try to write proposal_id through this relationship.
    contract = relationship(
        "Contract",
        primaryjoin=lambda: and_(
            foreign(Contract.proposal_id) == cast(Proposal.id, String),
            Contract.proposal_id != Contract.tracking_code,
        ),
        viewonly=True,
        uselist=False,
    )

    def __repr__(self):
        return f"<Proposal(id={self.id!r}, demand={self.demand_tracking_code!r}, status={self.status_title!r})>"
