"""Assign ``holding_company_code`` for شرکت مادرتخصصی مدیریت منابع آب ایران's
33 reporting-group members (Payam's list, 2026-09-27).

These are all fully independent employers (their own contracts, deposits,
balance) that are organizationally grouped under the holding company for
reporting only -- see the column's docstring in ``models/employer.py`` for
why this is deliberately NOT the same as ``parent_code``/Subsidiary roll-up.

Matching: the source file's names lack the "سهامی" (joint-stock) prefix
word that most of these carry in ``employers.name`` (e.g. file: "شرکت آب
منطقه‌ای تهران" vs DB: "شرکت سهامی آب منطقه‌ای تهران"), so exact-string
matching fails outright. Matched here by stripping a small set of common
corporate-form filler words before comparing, in addition to the
Arabic/Persian character normalization used throughout this project's other
import scripts (ي/ك -> ی/ک, ZWNJ/RTL marks -> plain space).

Two rows in the source file needed extra handling, both confirmed by hand:
  - "مدیریت منابع آب ایران" is the holding company's own row appearing
    inside its own subsidiary list -- skipped (it's reported as itself,
    not assigned a holding_company_code pointing to itself).
  - "شرکت توسعه منابع آب نيروي ايران" doesn't exist in `employers` at all
    (checked directly, zero matches under any spelling) -- reported as
    unmatched rather than guessed.
  - "چهار محال و بختياري" (two words) vs DB's "چهارمحال" (one word) is a
    genuine spelling difference needing an explicit alias below.

Usage: python scripts/import_holding_group_water.py [--apply]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import SessionLocal
from models.employer import Employer

SOURCE_FILE = Path(r"C:\Users\Payam\Downloads\شرکتهای زیرمجموعه مدیریت منابع آب.xlsx")
HOLDING_CODE = "219700"  # شرکت مادرتخصصی مدیریت منابع آب ایران

FILLER_WORDS = {"شرکت", "سهامی", "سازمان", "خاص", "عام"}

def normalize(name: str) -> str:
    text = str(name)
    text = text.replace(chr(0x200C), " ").replace(chr(0x064A), chr(0x06CC)).replace(chr(0x0643), chr(0x06A9))
    text = text.replace(chr(0x200F), "").replace(chr(0x200E), "")
    # "چهار محال" (two words, in the source file) vs "چهارمحال" (one word,
    # in `employers.name`) -- a substring fix so it works regardless of
    # surrounding filler words.
    text = text.replace("چهار محال", "چهارمحال")
    words = [w for w in text.split() if w not in FILLER_WORDS]
    return " ".join(words)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    df = pd.read_excel(SOURCE_FILE, sheet_name="Sheet1")

    db = SessionLocal()
    try:
        employers = db.query(Employer).filter(Employer.is_deleted == False).all()  # noqa: E712
        norm_map: dict[str, list[Employer]] = {}
        for e in employers:
            norm_map.setdefault(normalize(e.name), []).append(e)

        holding = db.query(Employer).filter(Employer.classification_code == HOLDING_CODE).one()
        print(f"holding: {holding.classification_code} {holding.name}")

        matched, ambiguous, unmatched = [], [], []
        for raw_name in df["عنوان شرکت"]:
            key = normalize(raw_name)
            candidates = norm_map.get(key, [])
            if len(candidates) == 1:
                matched.append((raw_name, candidates[0]))
            elif len(candidates) > 1:
                ambiguous.append((raw_name, candidates))
            else:
                unmatched.append(raw_name)

        print(f"\nmatched: {len(matched)} | ambiguous: {len(ambiguous)} | unmatched: {len(unmatched)}")

        if ambiguous:
            print("\n-- ambiguous --")
            for raw_name, cands in ambiguous:
                print(f"  {raw_name!r}:")
                for c in cands:
                    print(f"    {c.classification_code} {c.name}")

        if unmatched:
            print("\n-- unmatched --")
            for raw_name in unmatched:
                print(f"  {raw_name!r}")

        changed = []
        for raw_name, emp in matched:
            if emp.classification_code == HOLDING_CODE:
                continue  # the holding company itself, if it appears in its own list
            if emp.holding_company_code != HOLDING_CODE:
                changed.append((emp.classification_code, emp.name, emp.holding_company_code))
                emp.holding_company_code = HOLDING_CODE

        print(f"\nwill change: {len(changed)}")
        for code, name, old in changed:
            print(f"  {code} {name} (was: {old})")

        if args.apply:
            db.commit()
            print("\napplied.")
        else:
            db.rollback()
            print("\n(dry run -- nothing saved. pass --apply to write.)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
