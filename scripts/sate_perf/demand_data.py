"""Shared loader for the priority/demand records Payam exported from the
SATE system's own admin grid (``results/sate_perf/data/All_Demands.xlsx``,
sheet ``RadGridExport(1)``) -- one row per registered demand ("تقاضا"),
columns include the applicant employer's free-text name (``متقاضی``) and the
Jalali registration date (``تاریخ تقاضا``, ``YYYY/MM/DD`` text).

The ``متقاضی`` text does not always match ``employers.name`` exactly (e.g.
"آب منطقه ای هرمزگان" vs. the DB's "شرکت سهامی آب منطقه ای هرمزگان"), so
``match_employer`` does a normalized substring match to resolve the
``upper_organization`` (دستگاه بالادست) for the by-agency breakdown. Entries
that still don't resolve are bucketed as "سایر / نامشخص" -- this is a
best-effort join for a report chart, not an authoritative employer link.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.database import SessionLocal
from models.employer import Employer

DATA_PATH = Path(__file__).resolve().parents[2] / "results" / "sate_perf" / "data" / "All_Demands.xlsx"

COL_APPLICANT = "متقاضی"
COL_DATE = "تاریخ تقاضا"
UNMATCHED_LABEL = "سایر / نامشخص"

_STRIP_WORDS = ["شرکت سهامی", "شرکت مادر تخصصی", "شرکت", "سازمان", "مؤسسه", "موسسه"]


def _normalize(name: str) -> str:
    name = str(name).replace("‌", " ").strip()
    for word in _STRIP_WORDS:
        name = name.replace(word, "")
    return re.sub(r"\s+", " ", name).strip()


def load_demands(min_year: int = 1403, max_year: int = 1405) -> pd.DataFrame:
    df = pd.read_excel(DATA_PATH)
    df[COL_APPLICANT] = df[COL_APPLICANT].astype(str).str.strip()
    df["year"] = df[COL_DATE].astype(str).str.slice(0, 4).astype(int)
    return df[df["year"].between(min_year, max_year)].copy()


def build_employer_lookup():
    """Return (exact_name_to_agency, [(normalized_name, agency), ...])."""
    db = SessionLocal()
    try:
        employers = db.query(Employer.name, Employer.upper_organization).all()
    finally:
        db.close()
    exact = {name.strip(): agency for name, agency in employers}
    normalized = [(_normalize(name), agency) for name, agency in employers]
    return exact, normalized


def match_agency(applicant: str, exact_lookup, normalized_lookup) -> str:
    applicant = applicant.strip()
    if applicant in exact_lookup:
        return exact_lookup[applicant] or UNMATCHED_LABEL
    norm_applicant = _normalize(applicant)
    if not norm_applicant:
        return UNMATCHED_LABEL
    for norm_name, agency in normalized_lookup:
        if not norm_name:
            continue
        if norm_applicant == norm_name or norm_applicant in norm_name or norm_name in norm_applicant:
            return agency or UNMATCHED_LABEL
    if applicant.startswith("وزارت"):
        return applicant
    return UNMATCHED_LABEL
