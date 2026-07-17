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
def create_researcher(req: ResearcherCreate, db: Session = Depends(get_db)):
    """
    Register a new researcher (فناور).

    Business rule: a unique national_code is enforced before insert (including
    soft-deleted records). The model requires full_name, which is built by
    concatenating first_name and last_name.
    """
    existing = db.query(Researcher).filter(
        Researcher.national_code == req.national_code,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="خطا: فناور با این کد ملی قبلاً در سیستم ثبت شده است.",
        )

    university = db.query(University).filter(
        University.national_id == req.university_id,
        University.is_deleted == False,
    ).first()
    if not university:
        raise HTTPException(
            status_code=404,
            detail=f"دانشگاه/موسسه‌ای با شناسه ملی '{req.university_id}' یافت نشد.",
        )

    full_name = f"{req.first_name.strip()} {req.last_name.strip()}"

    researcher = Researcher(
        national_code=req.national_code,
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        full_name=full_name,
        mobile=req.mobile,
        email=req.email,
        academic_rank=req.academic_rank,
        education_level=req.education_level,
        researcher_type=req.researcher_type,
        university_id=req.university_id,
        status=req.status,
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
        national_code=researcher.national_code,
        full_name=researcher.full_name,
        university_id=researcher.university_id,
        academic_rank=researcher.academic_rank,
        education_level=researcher.education_level,
        researcher_type=researcher.researcher_type,
        status=researcher.status,
    )
