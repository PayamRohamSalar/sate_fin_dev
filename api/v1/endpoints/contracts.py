from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.researchers import Researcher
from models.university import University
from schemas.contract_schema import ContractSearchResult

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"]
)


@router.get("/search", response_model=List[ContractSearchResult])
def search_contracts(
    q: str = Query(..., min_length=1, description="Search term matched against tracking code or title"),
    db: Session = Depends(get_db),
):
    """
    Search active contracts for the payment auto-fill flow.

    Matches the query `q` (case-insensitive) against either the contract
    `tracking_code` or `title`. Only non-deleted contracts are returned, joined
    with their employer, university, and researcher to provide display names.

    **Parameters:**
    - `q`: Free-text search term (partial matches supported).

    **Returns:**
    - A list of matching contracts with denormalized employer, university, and
      researcher details for frontend auto-fill.
    """
    like_pattern = f"%{q}%"

    rows = (
        db.query(
            Contract.tracking_code.label("contract_tracking_code"),
            Contract.title.label("title"),
            Employer.name.label("employer_name"),
            Employer.classification_code.label("employer_classification_code"),
            University.name.label("university_name"),
            Researcher.full_name.label("researcher_name"),
        )
        .outerjoin(Employer, Contract.employer_code == Employer.classification_code)
        .outerjoin(University, Contract.university_id == University.national_id)
        .outerjoin(Researcher, Contract.researcher_id == Researcher.national_code)
        .filter(
            Contract.is_deleted == False,
            or_(
                Contract.tracking_code.ilike(like_pattern),
                Contract.title.ilike(like_pattern),
            ),
        )
        .all()
    )

    return [
        ContractSearchResult(
            contract_tracking_code=row.contract_tracking_code,
            title=row.title,
            employer_name=row.employer_name,
            employer_classification_code=row.employer_classification_code,
            university_name=row.university_name,
            researcher_name=row.researcher_name,
        )
        for row in rows
    ]
