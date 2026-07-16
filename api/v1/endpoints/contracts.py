from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.researchers import Researcher
from models.university import University
from schemas.contract_schema import ContractCreate, ContractSearchResult

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


@router.post("/", response_model=ContractSearchResult, status_code=201)
def create_contract(payload: ContractCreate, db: Session = Depends(get_db)):
    """
    Register a new contract.

    Business rule: subsidiary employers ("زیرمجموعه") are not allowed to
    contract directly; the contract must be registered under the parent
    (mother) company.
    """
    employer = db.query(Employer).filter(
        Employer.classification_code == payload.employer_classification_code,
        Employer.is_deleted == False,
    ).first()
    if not employer:
        raise HTTPException(status_code=404, detail=f"Employer with code '{payload.employer_classification_code}' not found.")

    if employer.employer_type == "Subsidiary":
        raise HTTPException(
            status_code=400,
            detail="خطا: شرکت‌های زیرمجموعه مجاز به انعقاد قرارداد نمی‌باشند. قرارداد باید به نام شرکت مادر ثبت شود.",
        )

    university = db.query(University).filter(
        University.national_id == payload.university_national_id,
        University.is_deleted == False,
    ).first()
    if not university:
        raise HTTPException(status_code=404, detail=f"University with national id '{payload.university_national_id}' not found.")

    researcher = db.query(Researcher).filter(
        Researcher.national_code == payload.researcher_national_id,
        Researcher.is_deleted == False,
    ).first()
    if not researcher:
        raise HTTPException(status_code=404, detail=f"Researcher with national code '{payload.researcher_national_id}' not found.")

    contract = Contract(
        tracking_code=payload.tracking_code,
        employer_code=payload.employer_classification_code,
        university_id=payload.university_national_id,
        researcher_id=payload.researcher_national_id,
        title=payload.title,
        total_amount=payload.total_amount,
        contract_date=payload.contract_date,
        duration_months=payload.duration_months,
        status="فعال",
        is_deleted=False,
    )
    db.add(contract)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Contract with tracking code '{payload.tracking_code}' already exists.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving contract: {e}")
    db.refresh(contract)

    return ContractSearchResult(
        contract_tracking_code=contract.tracking_code,
        title=contract.title,
        employer_name=employer.name,
        employer_classification_code=employer.classification_code,
        university_name=university.name,
        researcher_name=researcher.full_name,
    )
