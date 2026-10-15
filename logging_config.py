"""Non-sensitive logging setup for local and hosted runs."""

import logging

from travel_planner.config.settings import get_settings


def configure_logging() -> None:
    level = getattr(logging, get_settings().log_level, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
