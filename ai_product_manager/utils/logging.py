"""Logging setup for AI Product Manager."""
import logging
import os
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    level_name = (level or os.getenv("AIPM_LOG_LEVEL", "INFO")).upper()
    lvl = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
