from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.researchers import Researcher
from models.university import University
from schemas.researcher_schema import ResearcherCreate, ResearcherCreated

router = APIRouter(
    prefix="/researchers",
    tags=["Researchers"],
)


@router.get("/lookup", summary="Researcher lookup for dropdowns")
def researcher_lookup(db: Session = Depends(get_db)):
    """Return national_id + name for active researchers."""
    rows = db.query(Researcher.national_code, Researcher.full_name).filter(
        Researcher.is_deleted == False,
    ).order_by(Researcher.full_name).all()
    return [{"national_id": nc, "name": name} for nc, name in rows]


@router.post("/", response_model=ResearcherCreated, status_code=201)
def create_researcher(payload: ResearcherCreate, db: Session = Depends(get_db)):
    """
    Register a new researcher (فناور).

    Business rule: a unique national_id is enforced before insert (including
    soft-deleted records). The provided full_name is split into first/last name
    for the model's required columns.
    """
    existing = db.query(Researcher).filter(
        Researcher.national_code == payload.national_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="خطا: فناور با این کد ملی قبلاً در سیستم ثبت شده است.",
        )

    university = db.query(University).filter(
        University.national_id == payload.university_national_id,
        University.is_deleted == False,
    ).first()
    if not university:
        raise HTTPException(
            status_code=404,
            detail=f"دانشگاه/موسسه‌ای با شناسه ملی '{payload.university_national_id}' یافت نشد.",
        )

    name_parts = payload.full_name.strip().split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    researcher = Researcher(
        national_code=payload.national_id,
        first_name=first_name,
        last_name=last_name,
        full_name=payload.full_name.strip(),
        academic_rank=payload.academic_rank,
        university_id=payload.university_national_id,
        status="Active",
        is_deleted=False,
    )
    db.add(researcher)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="خطا: فناور با این کد ملی قبلاً در سیستم ثبت شده است.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving researcher: {e}")
    db.refresh(researcher)

    return ResearcherCreated(
        national_id=researcher.national_code,
        full_name=researcher.full_name,
        university_id=researcher.university_id,
        academic_rank=researcher.academic_rank,
        status=researcher.status,
    )
