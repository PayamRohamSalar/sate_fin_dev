"""One-off migration: standardize known university name variants.

The SATE Excel exports (e.g. ``data/Researchers_Add_In.xlsx``) reference
universities by their full official name, such as "دانشگاه علامه طباطبایی"
or "دانشگاه صنعتی شریف". Some rows already present in the ``universities``
table were loaded without the "دانشگاه " prefix, or with an alternate
Arabic/Persian spelling of the final "ی"/"ئ" character, so name-based
lookups (see ``scripts/import_researchers_upsert.py``) fail to match them.

This script renames each known variant to its canonical exact name using a
substring (``ILIKE``) search, so both the missing-prefix and the ی/ئ
spelling variant are caught by the same pattern.

Safety note: a substring match can be ambiguous. For example
``%صنعتی شریف%`` matches both the target record ("صنعتی شریف") and an
unrelated "پارک علم و فناوری دانشگاه صنعتی شریف" (a science & technology
park, not the university itself). To resolve this without guessing, each
rule first tries an *exact* (case-insensitive) name match against its
pattern; an exact hit is always the most specific possible match, so it is
used immediately without considering other substring matches. Only when no
exact match exists does the rule fall back to a substring (``ILIKE``)
search — and if that broader search still matches more than one active
row, the rule is reported and left untouched rather than risk renaming the
wrong organization.

Usage
-----
    python scripts/fix_university_names.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("fix_university_names")

# Name substring (matched with ILIKE, case-insensitive) -> canonical exact
# name. The substring stops just before the character that varies between
# known spellings (e.g. "طباطبا" is shared by both "طباطبایی" and
# "طباطبائی") so a single pattern catches the common variants.
NAME_FIX_MAPPING: dict[str, str] = {
    "علامه طباطبا": "دانشگاه علامه طباطبایی",
    "صنعتی شریف": "دانشگاه صنعتی شریف",
}


def find_exact_matching_universities(
    session: Session,
    name_pattern: str,
) -> list[University]:
    """Find active universities whose name exactly equals the pattern.

    An exact (case-insensitive) match is the most specific possible result,
    so callers should prefer it over a broader substring search.

    Args:
        session: Active SQLAlchemy session.
        name_pattern: The mapping rule's pattern, compared for equality.

    Returns:
        All active (``is_deleted == False``) universities whose name
        exactly equals ``name_pattern`` (case-insensitive).
    """
    return (
        session.query(University)
        .filter(
            University.is_deleted == False,  # noqa: E712
            University.name.ilike(name_pattern),
        )
        .all()
    )


def find_substring_matching_universities(
    session: Session,
    name_substring: str,
) -> list[University]:
    """Find active universities whose name contains the given substring.

    Args:
        session: Active SQLAlchemy session.
        name_substring: Substring to search for within ``University.name``.

    Returns:
        All active (``is_deleted == False``) universities whose name
        contains ``name_substring``.
    """
    return (
        session.query(University)
        .filter(
            University.is_deleted == False,  # noqa: E712
            University.name.ilike(f"%{name_substring}%"),
        )
        .all()
    )


def apply_name_fix(
    session: Session,
    name_substring: str,
    canonical_name: str,
) -> str:
    """Resolve one substring-to-canonical-name mapping rule.

    Lookup order, each unambiguous by construction, tried until one
    succeeds: (1) a row whose name already exactly equals
    ``canonical_name`` — the rule was already applied on a prior run;
    (2) a row whose name exactly equals ``name_substring`` — the
    not-yet-fixed variant; (3) only if neither exact lookup finds
    anything, a broader substring search, which is rejected if it turns
    out to match more than one active row.

    Args:
        session: Active SQLAlchemy session.
        name_substring: Substring (or exact name) identifying the
            university to rename.
        canonical_name: The exact standardized name to apply.

    Returns:
        One of ``"updated"``, ``"already_correct"``, ``"no_match"``, or
        ``"ambiguous"``, describing the outcome for this rule.
    """
    already_fixed = find_exact_matching_universities(session, canonical_name)
    if already_fixed:
        university = already_fixed[0]
        logger.info(
            "University '%s' (national_id=%s) already has the canonical "
            "name; no change needed.",
            canonical_name,
            university.national_id,
        )
        return "already_correct"

    matches = find_exact_matching_universities(session, name_substring)
    if not matches:
        matches = find_substring_matching_universities(session, name_substring)

    if not matches:
        logger.warning(
            "No active university matched pattern '%s'; skipped.",
            name_substring,
        )
        return "no_match"

    if len(matches) > 1:
        candidate_summary = ", ".join(
            f"{university.national_id}: '{university.name}'"
            for university in matches
        )
        logger.warning(
            "Pattern '%s' matched %d active universities (ambiguous, "
            "skipped): %s",
            name_substring,
            len(matches),
            candidate_summary,
        )
        return "ambiguous"

    university = matches[0]
    logger.info(
        "Renaming university national_id=%s: '%s' -> '%s'",
        university.national_id,
        university.name,
        canonical_name,
    )
    university.name = canonical_name
    return "updated"


def run_name_fix() -> None:
    """Apply every rule in ``NAME_FIX_MAPPING`` and print a final summary."""
    session = SessionLocal()
    outcome_counts = {
        "updated": 0,
        "already_correct": 0,
        "no_match": 0,
        "ambiguous": 0,
    }

    try:
        for name_substring, canonical_name in NAME_FIX_MAPPING.items():
            outcome = apply_name_fix(session, name_substring, canonical_name)
            outcome_counts[outcome] += 1
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Name fix failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("UNIVERSITY NAME FIX SUMMARY")
    print("=" * 60)
    print(f"Rules processed:            {len(NAME_FIX_MAPPING)}")
    print(f"Rows updated:               {outcome_counts['updated']}")
    print(f"Rows already correct:       {outcome_counts['already_correct']}")
    print(f"Rules with no match:        {outcome_counts['no_match']}")
    print(f"Rules skipped (ambiguous):  {outcome_counts['ambiguous']}")
    print("=" * 60)


if __name__ == "__main__":
    run_name_fix()
