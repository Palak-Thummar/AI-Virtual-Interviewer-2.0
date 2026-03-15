"""
Structured logging configuration for CareerIQ backend.
Provides consistent log formatting across all modules.
"""

import logging
import sys
from datetime import datetime, timezone


class UTCFormatter(logging.Formatter):
    """Log formatter that always uses UTC timestamps."""

    converter = lambda *args: datetime.now(timezone.utc).timetuple()

    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created, tz=timezone.utc)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(record.msecs):03d}Z"


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application-wide structured logging.
    Call once at startup in main.py.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = UTCFormatter(
        fmt="[%(asctime)s] %(levelname)-8s %(name)s — %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Replace existing handlers so we don't duplicate output
    if root.handlers:
        root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (use __name__ in each module)."""
    return logging.getLogger(name)
