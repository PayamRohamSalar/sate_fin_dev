"""Demand/Proposal analytics for the SATE financial system.

Kept separate from ``services.financial_engine`` (mandate/deposit/contract/
payment money-flow logic) because this is a different domain -- who asked
for what research (``Demand``), who answered (``Proposal``), and whether
that answer became a contract. The only touchpoint with the financial
domain is the proposal-to-contract link, which is read here read-only via
``Contract.proposal_id`` (see that column's comment in ``models/contract.py``
for why it isn't a declared foreign key).
"""

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.contract import Contract
from models.demand import Demand
from models.employer import Employer
from models.proposal import Proposal

STATUS_ORDER = [
    "ذخیره موقت",
    "در انتظار تایید متقاضی",
    "در انتظار تایید موسسه / دانشگاه",
    "تایید نهایی",
    "رد",
]


def get_proposal_details(db: Session) -> pd.DataFrame:
    """One row per proposal, enriched with the employer behind its demand
    and whether it led to a contract.

    This is the single base table for every view in the "تقاضا و پیشنهاده"
    dashboard (status breakdown, submission trend, employer/researcher
    ranking, approval-to-contract conversion) so none of those views can
    ever disagree with each other about the underlying numbers.

    Returns:
        A DataFrame with columns: ``proposal_id``, ``demand_tracking_code``,
        ``demand_title``, ``employer_code``, ``employer_name``,
        ``researcher_name``, ``researcher_code``, ``university_name``,
        ``university_id``, ``status_code``, ``status_title``,
        ``submitted_at``, ``has_contract`` (bool), ``contract_tracking_code``
        (the first linked contract, if any), ``contract_count`` (normally 0
        or 1; a handful of proposals have more than one contract pointing
        at them -- see ``models/contract.py``'s ``proposal_id`` comment).
    """
    rows = db.execute(
        select(
            Proposal.id,
            Proposal.demand_tracking_code,
            Proposal.researcher_name,
            Proposal.researcher_code,
            Proposal.university_name,
            Proposal.university_id,
            Proposal.status_code,
            Proposal.status_title,
            Proposal.submitted_at,
            Demand.title,
            Demand.employer_code,
            Employer.name,
        )
        .select_from(Proposal)
        .outerjoin(Demand, Proposal.demand_tracking_code == Demand.tracking_code)
        .outerjoin(Employer, Demand.employer_code == Employer.classification_code)
        .where(Proposal.is_deleted == False)  # noqa: E712
    ).all()

    contract_links = (
        db.query(Contract.proposal_id, Contract.tracking_code)
        .filter(
            Contract.proposal_id.isnot(None),
            Contract.proposal_id != Contract.tracking_code,
            Contract.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    contracts_by_proposal: dict[int, list[str]] = {}
    for proposal_id_raw, tracking_code in contract_links:
        try:
            proposal_id = int(proposal_id_raw)
        except (TypeError, ValueError):
            continue
        contracts_by_proposal.setdefault(proposal_id, []).append(tracking_code)

    records = []
    for (
        proposal_id, demand_tracking_code, researcher_name, researcher_code,
        university_name, university_id, status_code, status_title, submitted_at,
        demand_title, employer_code, employer_name,
    ) in rows:
        linked_contracts = contracts_by_proposal.get(proposal_id, [])
        records.append({
            "proposal_id": proposal_id,
            "demand_tracking_code": demand_tracking_code,
            "demand_title": demand_title,
            "employer_code": employer_code,
            "employer_name": employer_name,
            "researcher_name": researcher_name,
            "researcher_code": researcher_code,
            "university_name": university_name,
            "university_id": university_id,
            "status_code": status_code,
            "status_title": status_title,
            "submitted_at": submitted_at,
            "has_contract": len(linked_contracts) > 0,
            "contract_tracking_code": linked_contracts[0] if linked_contracts else None,
            "contract_count": len(linked_contracts),
        })

    columns = [
        "proposal_id", "demand_tracking_code", "demand_title", "employer_code",
        "employer_name", "researcher_name", "researcher_code", "university_name",
        "university_id", "status_code", "status_title", "submitted_at",
        "has_contract", "contract_tracking_code", "contract_count",
    ]
    return pd.DataFrame.from_records(records, columns=columns)
