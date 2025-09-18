"""Migration CLI for AI Product Manager.

Usage examples:
- ai-pm-db upgrade head
- ai-pm-db downgrade -1
- ai-pm-db revision -m "add research fields" --autogenerate
"""
from __future__ import annotations
import os
import sys
import argparse
from alembic import command
from alembic.config import Config


def _alembic_config() -> Config:
    # Point to the packaged alembic.ini inside ai_product_manager
    base_dir = os.path.dirname(os.path.dirname(__file__))
    ini_path = os.path.join(base_dir, "alembic.ini")
    if not os.path.isfile(ini_path):
        raise RuntimeError(f"alembic.ini not found at {ini_path}")
    cfg = Config(ini_path)
    # Ensure script_location is relative to package path
    cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
    # Respect env var for DB URL if set, else let our env.py use get_engine()
    db_url = os.getenv("AIPM_DB_URL")
    if db_url:
        cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="AI PM DB migration CLI (Alembic)")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    p_upgrade = subparsers.add_parser("upgrade", help="Upgrade to a target revision (e.g., head)")
    p_upgrade.add_argument("revision", help="Target revision, e.g. head or base..head")

    p_downgrade = subparsers.add_parser("downgrade", help="Downgrade to a target revision")
    p_downgrade.add_argument("revision", help="Target revision, e.g. -1 or base")

    p_rev = subparsers.add_parser("revision", help="Create a new revision")
    p_rev.add_argument("-m", "--message", required=True, help="Revision message")
    p_rev.add_argument("--autogenerate", action="store_true", help="Autogenerate changes from models")

    args = parser.parse_args(argv)
    cfg = _alembic_config()

    if args.cmd == "upgrade":
        command.upgrade(cfg, args.revision)
    elif args.cmd == "downgrade":
        command.downgrade(cfg, args.revision)
    elif args.cmd == "revision":
        command.revision(cfg, message=args.message, autogenerate=args.autogenerate)
    else:
        parser.print_help()


if __name__ == "__main__":
    main(sys.argv[1:])
