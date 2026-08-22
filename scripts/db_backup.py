"""Cross-machine PostgreSQL backup for the SATE database.

Dumps the local ``sate_db`` (custom format, ``-Fc``) into
``data/Archive/db_backups/``, which is synced by OneDrive between the PC and
laptop copies of this project. The dump filename is tagged with the local
hostname and timestamp so backups from either machine never collide, and a
``latest_backup.json`` manifest records which file is newest, who produced
it, and the row counts at dump time — this is what
``db_restore_from_backup.py`` on the other machine reads to decide whether a
pull is needed and to verify the restore afterwards.

Run this after a work session on whichever machine just received new data
(e.g. contracts entered through the web forms, or ad-hoc correction scripts).
It does not touch the source database — dump-only, read-only.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text

from core.database import DATABASE_URL, engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "data" / "Archive" / "db_backups"
MANIFEST_PATH = BACKUP_DIR / "latest_backup.json"
RETENTION = 30  # keep the newest N dated backups; manifest + prerestore files are exempt


def find_pg_binary(name: str) -> str:
    """Locate a PostgreSQL client binary (e.g. pg_dump) on PATH or under the
    standard Windows install location, since the install path/version can
    differ between the PC and the laptop."""
    on_path = shutil.which(name)
    if on_path:
        return on_path

    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    pg_root = program_files / "PostgreSQL"
    if pg_root.is_dir():
        candidates = sorted(pg_root.glob(f"*/bin/{name}.exe"), reverse=True)
        if candidates:
            return str(candidates[0])

    raise FileNotFoundError(
        f"Could not find {name}.exe on PATH or under {pg_root}. "
        "Install the PostgreSQL client tools or add them to PATH."
    )


def get_table_counts() -> dict:
    """Row counts for every table in the public schema, for the manifest."""
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names(schema="public"))
    counts = {}
    with engine.connect() as conn:
        for table in tables:
            counts[table] = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    return counts


def prune_old_backups() -> None:
    """Keep only the newest RETENTION dated backups so OneDrive doesn't
    accumulate an unbounded number of dumps. Pre-restore safety dumps use a
    different filename prefix and are left alone."""
    dumps = sorted(BACKUP_DIR.glob("sate_db_backup_*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in dumps[RETENTION:]:
        stale.unlink()
        print(f"   Pruned old backup: {stale.name}")


def main() -> int:
    print("=" * 60)
    print("SATE DB Backup")
    print("=" * 60)

    hostname = socket.gethostname()
    timestamp = datetime.now()
    filename = f"sate_db_backup_{hostname}_{timestamp:%Y%m%d_%H%M%S}.dump"

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dump_path = BACKUP_DIR / filename

    print(f"\n1. Counting rows in {DATABASE_URL.split('@')[-1]}...")
    try:
        table_counts = get_table_counts()
    except Exception as exc:
        print(f"Error querying the database: {exc}")
        return 1
    for table, count in table_counts.items():
        print(f"   {table}: {count}")

    print(f"\n2. Dumping to {dump_path}...")
    pg_dump = find_pg_binary("pg_dump")
    result = subprocess.run(
        [pg_dump, "-d", DATABASE_URL, "-Fc", "-f", str(dump_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"pg_dump failed:\n{result.stderr}")
        dump_path.unlink(missing_ok=True)
        return 1

    file_size = dump_path.stat().st_size
    print(f"   Done: {file_size:,} bytes")

    print("\n3. Writing manifest...")
    manifest = {
        "filename": filename,
        "hostname": hostname,
        "created_at": timestamp.isoformat(),
        "file_size_bytes": file_size,
        "table_counts": table_counts,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n4. Pruning old backups...")
    prune_old_backups()

    print("\n" + "=" * 60)
    print(f"Backup complete: {dump_path}")
    print(f"Run db_restore_from_backup.py on the other machine to pull this in.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
