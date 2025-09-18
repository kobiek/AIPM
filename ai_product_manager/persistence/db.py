"""Database setup for SQLModel (SQLite)."""
from contextlib import contextmanager
from typing import Iterator
from sqlmodel import SQLModel, Session
from sqlalchemy import create_engine, text
import os

try:
    from alembic import command as _alembic_command  # type: ignore
    from alembic.config import Config as _AlembicConfig  # type: ignore
except Exception:  # pragma: no cover
    _alembic_command = None
    _AlembicConfig = None

_ENGINE = None
_DB_URL = None


def get_engine(echo: bool = False):
    global _ENGINE, _DB_URL
    if _ENGINE is None:
        # Default DB path in project directory
        db_path = os.getenv("AIPM_DB_PATH", os.path.join(os.getcwd(), "aipm.db"))
        _DB_URL = f"sqlite:///{db_path}"
        _ENGINE = create_engine(_DB_URL, echo=echo)
    return _ENGINE


def _migrate(engine) -> None:
    """Lightweight migrations to add missing columns if the DB already exists."""
    with engine.connect() as conn:
        # Get existing columns for hypothesismodel
        try:
            res = conn.execute(text("PRAGMA table_info(hypothesismodel)"))
            cols = {row[1] for row in res}
            # Add new columns if missing
            add_cols = []
            if "current" not in cols:
                conn.execute(text("ALTER TABLE hypothesismodel ADD COLUMN current REAL"))
            if "delta" not in cols:
                conn.execute(text("ALTER TABLE hypothesismodel ADD COLUMN delta REAL"))
            if "evaluated_at" not in cols:
                conn.execute(text("ALTER TABLE hypothesismodel ADD COLUMN evaluated_at TIMESTAMP"))
            if "notes" not in cols:
                conn.execute(text("ALTER TABLE hypothesismodel ADD COLUMN notes TEXT"))
        except Exception:
            # Table may not exist yet; ignore and let create_all handle it
            pass
        # ResearchItemModel columns: tags, note
        try:
            res = conn.execute(text("PRAGMA table_info(researchitemmodel)"))
            cols = {row[1] for row in res}
            if "tags" not in cols:
                conn.execute(text("ALTER TABLE researchitemmodel ADD COLUMN tags TEXT"))
            if "note" not in cols:
                conn.execute(text("ALTER TABLE researchitemmodel ADD COLUMN note TEXT"))
            if "feature_id" not in cols:
                conn.execute(text("ALTER TABLE researchitemmodel ADD COLUMN feature_id TEXT"))
            if "objective_id" not in cols:
                conn.execute(text("ALTER TABLE researchitemmodel ADD COLUMN objective_id TEXT"))
            if "processed" not in cols:
                conn.execute(text("ALTER TABLE researchitemmodel ADD COLUMN processed BOOLEAN DEFAULT 0"))
        except Exception:
            pass


def _alembic_upgrade_head() -> bool:
    """Attempt to run Alembic upgrade head. Returns True on success."""
    if not (_alembic_command and _AlembicConfig):
        return False
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))  # ai_product_manager/
        ini_path = os.path.join(base_dir, "alembic.ini")
        if not os.path.isfile(ini_path):
            return False
        cfg = _AlembicConfig(ini_path)
        cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
        # Respect AIPM_DB_URL if present
        db_url = os.getenv("AIPM_DB_URL")
        if db_url:
            cfg.set_main_option("sqlalchemy.url", db_url)
        _alembic_command.upgrade(cfg, "head")
        return True
    except Exception:
        return False


def init_db(echo: bool = False) -> None:
    engine = get_engine(echo=echo)
    # Try alembic migrations first
    if not _alembic_upgrade_head():
        # Fallback: create tables and run lightweight column migrations for dev
        SQLModel.metadata.create_all(engine)
        _migrate(engine)


@contextmanager
def get_session(echo: bool = False) -> Iterator[Session]:
    engine = get_engine(echo=echo)
    with Session(engine) as session:
        yield session
