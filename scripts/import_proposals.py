"""Import proposals ("پیشنهاده‌ها") from a raw view export (vw_proposals.csv).

The source file is a straight CSV dump of a SQL view and has two known
quirks handled by ``_reconstruct_rows`` below:

  1. Some long free-text fields contain a raw (unescaped, unquoted)
     newline, which splits one logical record across two physical lines.
  2. A handful of rows contain an unescaped comma inside a field, which
     produces extra columns instead of a line break.

Both are repaired by realigning to the known 17-column header before any
row is used, rather than dropping the affected records. See git history /
project memory for the CSV forensics that validated this approach (100%
of the recovered rows produced a valid integer ``ID``, and the one
previously-corrupted row this was tested against reconstructed correctly).

Idempotent: existing proposal ``id``s are skipped, so re-running after
adding new rows to the source file only imports the new ones.

Usage: python scripts/import_proposals.py [path/to/vw_proposals.csv]
"""

import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import Base, SessionLocal, engine
from models.demand import Demand  # noqa: F401 -- registers ORM relationship target
from models.proposal import Proposal
from models.researchers import Researcher
from models.university import University

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[1] / "results" / "sate_perf" / "data" / "vw_proposals.csv"
NCOLS = 17
BATCH_SIZE = 500


def _reconstruct_rows(path: Path):
    """Yield well-formed 17-column rows from the raw (quirky) CSV.

    See the module docstring for why this is needed instead of a plain
    ``csv.reader`` / ``pandas.read_csv`` call.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if len(header) != NCOLS:
            raise ValueError(f"Expected {NCOLS} columns, got {len(header)}: {header}")

        buffer = None
        for row in reader:
            if buffer is not None:
                first = row[0] if row else ""
                rest = row[1:] if row else []
                buffer = buffer[:-1] + [buffer[-1] + "\n" + first] + rest
                row, buffer = buffer, None

            if len(row) == NCOLS:
                yield header, row
            elif len(row) < NCOLS:
                buffer = row
            else:
                # Extra columns: an unescaped comma landed inside Abstract
                # (column index 2) -- ID and trm_Request_ID (0, 1) are pure
                # integers and never contain commas, so it's safe to fold
                # every extra field back into index 2.
                extra = len(row) - NCOLS
                fixed = row[:2] + [",".join(row[2:2 + extra + 1])] + row[2 + extra + 1:]
                yield header, fixed

        if buffer is not None:
            raise ValueError(f"Unresolved multi-line field at end of file: {buffer!r}")


def _clean_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def import_proposals(csv_path: Path = DEFAULT_CSV_PATH) -> None:
    Base.metadata.create_all(bind=engine, tables=[Proposal.__table__])

    print(f"Reading: {csv_path}")
    header = None
    records = []
    for header, row in _reconstruct_rows(csv_path):
        records.append(row)
    df = pd.DataFrame(records, columns=header)
    print(f"[OK] Reconstructed {len(df)} rows")

    db = SessionLocal()
    try:
        researcher_name_to_code = {
            r.full_name.strip(): r.national_code
            for r in db.query(Researcher).filter(Researcher.is_deleted == False).all()  # noqa: E712
        }
        university_name_to_id = {
            u.name.strip(): u.national_id
            for u in db.query(University).filter(University.is_deleted == False).all()  # noqa: E712
        }
        existing_ids = {pid for (pid,) in db.query(Proposal.id).all()}
        print(f"[OK] {len(existing_ids)} proposals already in database (will be skipped)")

        added = 0
        skipped_duplicate = 0
        skipped_invalid = 0
        matched_researcher = 0
        matched_university = 0

        for _, row in df.iterrows():
            try:
                proposal_id = int(row["ID"])
            except (TypeError, ValueError):
                skipped_invalid += 1
                continue

            if proposal_id in existing_ids:
                skipped_duplicate += 1
                continue

            try:
                demand_tracking_code = str(int(float(row["trm_Request_ID"])))
            except (TypeError, ValueError):
                demand_tracking_code = None

            researcher_name = _clean_str(row.get("lk_Contractor"))
            university_name = _clean_str(row.get("lk_UniversityTitle"))
            researcher_code = researcher_name_to_code.get(researcher_name) if researcher_name else None
            university_id = university_name_to_id.get(university_name) if university_name else None
            if researcher_code:
                matched_researcher += 1
            if university_id:
                matched_university += 1

            status_code = row.get("lk_StatusID")
            try:
                status_code = int(float(status_code))
            except (TypeError, ValueError):
                status_code = None

            submitted_at = pd.to_datetime(row.get("CreateDate"), errors="coerce")
            submitted_at = None if pd.isna(submitted_at) else submitted_at.to_pydatetime()

            proposal = Proposal(
                id=proposal_id,
                demand_tracking_code=demand_tracking_code,
                researcher_name=researcher_name or "نامشخص",
                researcher_code=researcher_code,
                university_name=university_name,
                university_id=university_id,
                status_code=status_code,
                status_title=_clean_str(row.get("lk_StatusTitle")),
                submitted_at=submitted_at,
            )
            db.add(proposal)
            existing_ids.add(proposal_id)
            added += 1

            if added % BATCH_SIZE == 0:
                db.commit()
                print(f"  Progress: {added} proposals added")

        db.commit()

        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"[OK] Imported: {added} proposals")
        print(f"[OK] Resolved to an existing researcher_code: {matched_researcher}/{added}")
        print(f"[OK] Resolved to an existing university_id: {matched_university}/{added}")
        print(f"[SKIP] Already in database: {skipped_duplicate}")
        print(f"[SKIP] Unparseable ID: {skipped_invalid}")
        print(f"Total rows reconstructed from source file: {len(df)}")
        print("=" * 60)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV_PATH
    import_proposals(path)
