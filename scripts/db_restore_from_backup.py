"""Pull the other machine's latest SATE DB backup into the local database.

Companion to ``db_backup.py``. Looks at ``data/Archive/db_backups/`` (synced
by OneDrive) for the newest dump produced by a *different* hostname than this
machine, and — after confirmation — replaces the local ``sate_db`` with it:
drops and recreates the database, restores the dump, then verifies row
counts against the manifest written at backup time.

This is a one-way pull, snapshot-based sync: it makes the local database
match whatever was backed up on the other machine at backup time. It is
destructive to whatever is currently in the local database, so a safety dump
of the current local state is always taken first (prefixed
``sate_db_prerestore_``), and the actual drop/restore step asks for
confirmation unless ``--yes`` is passed.

Usage:
    python scripts/db_restore_from_backup.py            # asks for confirmation
    python scripts/db_restore_from_backup.py --yes       # no prompt
    python scripts/db_restore_from_backup.py --file path/to/specific.dump
"""

import argparse
import json
import re
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

from core.database import DATABASE_URL, engine
from db_backup import BACKUP_DIR, MANIFEST_PATH, find_pg_binary, get_table_counts

STATE_DIR = BACKUP_DIR / ".state"

# db_backup.py always names files sate_db_backup_<hostname>_<YYYYMMDD_HHMMSS>.dump.
# Anything else (e.g. a dump made manually before this tooling existed) doesn't
# carry a reliable hostname tag and must not be auto-treated as "from another
# machine" — the hostname group is required, not just absence of our own name.
BACKUP_NAME_RE = re.compile(r"^sate_db_backup_(?P<hostname>.+)_\d{8}_\d{6}\.dump$")


def backup_hostname(path: Path) -> str | None:
    match = BACKUP_NAME_RE.match(path.name)
    return match.group("hostname") if match else None


def pick_candidate(explicit_file: str | None, hostname: str) -> tuple[Path, dict | None]:
    """Return the dump to restore and its manifest info (if available)."""
    if explicit_file:
        path = Path(explicit_file)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: {path}")
        return path, None

    manifest = None
    if MANIFEST_PATH.is_file():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.get("hostname") != hostname:
            candidate = BACKUP_DIR / manifest["filename"]
            if candidate.is_file():
                return candidate, manifest

    # Manifest missing, stale, or produced by this same machine: fall back to
    # the newest dump on disk that is tagged with a *different* hostname.
    # Files that don't match the tool's naming pattern (e.g. a manual dump
    # made before this tooling existed) are ignored, not assumed foreign.
    others = [
        p for p in BACKUP_DIR.glob("sate_db_backup_*.dump")
        if (h := backup_hostname(p)) is not None and h != hostname
    ]
    if not others:
        raise FileNotFoundError(
            f"No backup from another machine found in {BACKUP_DIR}. "
            "Run db_backup.py on the source machine first."
        )
    newest = max(others, key=lambda p: p.stat().st_mtime)
    return newest, None


def already_applied(filename: str, hostname: str) -> bool:
    marker = STATE_DIR / f"{hostname}_last_restored.txt"
    return marker.is_file() and marker.read_text(encoding="utf-8").strip() == filename


def mark_applied(filename: str, hostname: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    marker = STATE_DIR / f"{hostname}_last_restored.txt"
    marker.write_text(filename, encoding="utf-8")


def safety_backup(hostname: str) -> Path:
    """Dump the current local DB before overwriting it, so nothing entered
    only on this machine (e.g. via the web forms) is lost irrecoverably."""
    timestamp = datetime.now()
    path = BACKUP_DIR / f"sate_db_prerestore_{hostname}_{timestamp:%Y%m%d_%H%M%S}.dump"
    pg_dump = find_pg_binary("pg_dump")
    result = subprocess.run(
        [pg_dump, "-d", DATABASE_URL, "-Fc", "-f", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Safety pre-restore backup failed, aborting restore:\n{result.stderr}")
    return path


def recreate_database(maint_url: str, dbname: str) -> None:
    psql = find_pg_binary("psql")
    # Each statement needs its own -c: psql sends a multi-statement -c string as
    # one implicit transaction, and DROP/CREATE DATABASE can't run inside one.
    statements = [
        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{dbname}' AND pid <> pg_backend_pid();",
        f'DROP DATABASE IF EXISTS "{dbname}";',
        f'CREATE DATABASE "{dbname}";',
    ]
    for sql in statements:
        result = subprocess.run(
            [psql, "-d", maint_url, "-v", "ON_ERROR_STOP=1", "-c", sql],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to drop/recreate database:\n{result.stderr}")


def restore_dump(dump_path: Path) -> None:
    pg_restore = find_pg_binary("pg_restore")
    result = subprocess.run(
        [pg_restore, "-d", DATABASE_URL, "--no-owner", "--no-privileges", str(dump_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pg_restore failed:\n{result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", "-y", action="store_true", help="skip the confirmation prompt")
    parser.add_argument("--file", help="restore a specific dump file instead of auto-detecting the newest one")
    args = parser.parse_args()

    print("=" * 60)
    print("SATE DB Restore (pull from other machine)")
    print("=" * 60)

    hostname = socket.gethostname()

    print("\n1. Locating candidate backup...")
    try:
        dump_path, manifest = pick_candidate(args.file, hostname)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    print(f"   Candidate: {dump_path.name}")
    if manifest:
        print(f"   From host: {manifest['hostname']}, created: {manifest['created_at']}")

    if already_applied(dump_path.name, hostname):
        print(f"\nAlready up to date — {dump_path.name} was already restored on this machine.")
        return 0

    print("\n2. This will DROP and recreate the local sate_db, replacing all data with the backup above.")
    print("   A safety dump of the current local database will be taken first.")
    if not args.yes:
        answer = input("   Proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    print("\n3. Taking safety pre-restore backup of current local database...")
    safety_path = safety_backup(hostname)
    print(f"   Saved: {safety_path.name}")

    dbname = make_url(DATABASE_URL).database
    # str(url) masks the password as "***" in SQLAlchemy 2.x, which breaks psql auth.
    maint_url = make_url(DATABASE_URL).set(database="postgres").render_as_string(hide_password=False)

    print(f"\n4. Dropping and recreating '{dbname}'...")
    try:
        recreate_database(maint_url, dbname)
    except RuntimeError as exc:
        print(str(exc))
        print(f"Local database left untouched or partially dropped. Safety backup: {safety_path}")
        return 1
    print("   Done.")

    print(f"\n5. Restoring from {dump_path.name}...")
    try:
        restore_dump(dump_path)
    except RuntimeError as exc:
        print(str(exc))
        print(f"Database may be left empty/partial. Restore manually from: {safety_path}")
        return 1
    print("   Done.")

    print("\n6. Verifying row counts...")
    actual_counts = get_table_counts()
    expected_counts = manifest["table_counts"] if manifest else None
    mismatch = False
    for table, count in actual_counts.items():
        expected = expected_counts.get(table) if expected_counts else None
        if expected is None:
            print(f"   {table}: {count}")
        elif count == expected:
            print(f"   {table}: {count} (matches source)")
        else:
            print(f"   {table}: {count} (source had {expected} — MISMATCH)")
            mismatch = True

    mark_applied(dump_path.name, hostname)

    print("\n" + "=" * 60)
    if mismatch:
        print("Restore completed WITH MISMATCHES — investigate before trusting this data.")
    else:
        print("Restore completed successfully. Local database now matches the source machine.")
    print(f"Pre-restore safety backup kept at: {safety_path}")
    print("=" * 60)
    return 1 if mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())
