"""Apply data/migrations/*.sql in order, once each, recorded in schema_migrations (plan v2.2 section 12).

    cd engine && PYTHONPATH=.. uv run python ../data/migrate.py            # apply what is new
    cd engine && PYTHONPATH=.. uv run python ../data/migrate.py --status   # list applied / pending
    cd engine && PYTHONPATH=.. uv run python ../data/migrate.py --db <url> # another database (Cloud SQL via the proxy)

Migrations are forward-only and additive (no DROP TABLE, no renames). Each runs in its own transaction; a file that
changed after it was applied is reported, not re-run. Back up Cloud SQL first: gcloud sql backups create --instance ...
"""
import argparse
import hashlib
import os
import re
from pathlib import Path

import psycopg

HERE = Path(__file__).parent / "migrations"
DESTRUCTIVE = re.compile(r"\bDROP\s+(TABLE|COLUMN|SCHEMA|DATABASE)\b|\bTRUNCATE\b|\bRENAME\b", re.IGNORECASE)


def files() -> list[Path]:
    return sorted(HERE.glob("[0-9][0-9][0-9]_*.sql"))


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_additive(path: Path) -> None:
    body = re.sub(r"--[^\n]*", "", path.read_text())
    if DESTRUCTIVE.search(body):
        raise SystemExit(f"{path.name} contains a destructive statement; migrations must be additive")


def connect(url: str | None) -> psycopg.Connection:
    if url:
        return psycopg.connect(url, autocommit=True)
    from engine import store

    return psycopg.connect(**store.connect_kwargs(), autocommit=True)  # each file commits on its own


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=None, help="Postgres URL (default: DATABASE_URL / Cloud SQL socket)")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    if args.db:  # the registry sync below goes through engine.store, which reads DATABASE_URL
        os.environ["DATABASE_URL"] = args.db
        os.environ.pop("CLOUD_SQL_INSTANCE", None)
    with connect(args.db or os.environ.get("DATABASE_URL")) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, checksum TEXT NOT NULL,
                                                                     applied_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        applied = {r[0]: r[1] for r in conn.execute("SELECT name, checksum FROM schema_migrations").fetchall()}
        for path in files():
            check_additive(path)
            if path.name in applied:
                note = "" if applied[path.name] == checksum(path) else "  (file changed since it was applied!)"
                print(f"applied  {path.name}{note}")
                continue
            if args.status:
                print(f"pending  {path.name}")
                continue
            with conn.transaction():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO schema_migrations (name, checksum) VALUES (%s, %s)",
                             (path.name, checksum(path)))
            print(f"applied  {path.name}  (now)")
    if not args.status:
        try:  # the source registry (data/source_registry_japac.yaml) into source_registry
            from engine.sources import registry
            print(f"source registry: {registry.sync_to_db()} sources synced")
        except Exception as error:  # noqa: BLE001  run from engine/ with PYTHONPATH=.. to include this step
            print(f"source registry not synced ({type(error).__name__})")


if __name__ == "__main__":
    main()
