"""CI helper: fail if Alembic autogenerate would create a new revision.

Strategy:
- Capture current files in alembic/versions
- Run `alembic revision --autogenerate`
- If a new file appears, delete it and exit(1)
- Else exit(0)
"""
from __future__ import annotations
import os
import sys
import time
from typing import List
from alembic import command
from alembic.config import Config


def _alembic_config() -> Config:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ini_path = os.path.join(base_dir, "alembic.ini")
    if not os.path.isfile(ini_path):
        raise RuntimeError(f"alembic.ini not found at {ini_path}")
    cfg = Config(ini_path)
    cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
    db_url = os.getenv("AIPM_DB_URL")
    if db_url:
        cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def main(argv: List[str] | None = None) -> None:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    versions_dir = os.path.join(base_dir, "alembic", "versions")
    os.makedirs(versions_dir, exist_ok=True)

    before = set(f for f in os.listdir(versions_dir) if f.endswith(".py"))

    cfg = _alembic_config()
    # unique message including timestamp
    msg = f"autogen check {int(time.time())}"
    # Generate revision (may or may not create a file depending on diffs)
    command.revision(cfg, message=msg, autogenerate=True)

    after = set(f for f in os.listdir(versions_dir) if f.endswith(".py"))
    created = sorted(after - before)
    if created:
        # Clean up created files to keep repo clean
        for fname in created:
            try:
                os.remove(os.path.join(versions_dir, fname))
            except Exception:
                pass
        print("Migration drift detected: model changes not covered by migrations.")
        print("Created (and removed) revisions:", ", ".join(created))
        sys.exit(1)
    else:
        print("Migrations are up to date.")
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
