from __future__ import annotations
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import our SQLModel metadata and engine factory
from ai_product_manager.persistence.db import get_engine
from ai_product_manager.persistence import models as app_models
from sqlmodel import SQLModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name and os.path.exists(config.config_file_name):
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# Using SQLModel metadata which includes all models

# Ensure all models are imported so their tables are registered on metadata
_ = app_models  # noqa: F401

target_metadata = SQLModel.metadata

def include_object(object, name, type_, reflected, compare_to):
    # Only include our app tables (heuristic: end with 'model' or specific known names)
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    # We don't rely on URL from .ini; this path is primarily for debugging
    url = os.getenv("AIPM_DB_URL", "sqlite:///aipm.db")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    engine = get_engine()
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
