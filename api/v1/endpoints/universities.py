from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.university import University
from schemas.university_schema import UniversityCreate, UniversityCreated

router = APIRouter(
    prefix="/universities",
    tags=["Universities"],
)


@router.get("/lookup", summary="University lookup for dropdowns")
def university_lookup(db: Session = Depends(get_db)):
    """Return national_id + name for active universities."""
    rows = db.query(University.national_id, University.name).filter(
        University.is_deleted == False,
    ).order_by(University.name).all()
    return [{"national_id": nid, "name": name} for nid, name in rows]


@router.post("/", response_model=UniversityCreated, status_code=201)
def create_university(payload: UniversityCreate, db: Session = Depends(get_db)):
    """
    Register a new university / executing institution.

    Business rule: a unique national_id is enforced before insert (including
    soft-deleted records) to avoid re-registration conflicts.
    """
    existing = db.query(University).filter(
        University.national_id == payload.national_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="خطا: موسسه‌ای با این شناسه ملی قبلاً در سیستم ثبت شده است.",
        )

    university = University(
        national_id=payload.national_id,
        name=payload.name,
        province=payload.province,
        university_type=payload.university_type,
        status="Active" if payload.is_active else "Inactive",
        is_deleted=False,
    )
    db.add(university)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="خطا: موسسه‌ای با این شناسه ملی قبلاً در سیستم ثبت شده است.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving university: {e}")
    db.refresh(university)

    return UniversityCreated(
        national_id=university.national_id,
        name=university.name,
        province=university.province,
        university_type=university.university_type,
        status=university.status,
    )
