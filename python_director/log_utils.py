from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from pathlib import Path


_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.getenv("DIRECTOR_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    log_file = os.getenv("DIRECTOR_LOG_FILE")
    log_path = (
        Path(log_file).expanduser()
        if log_file
        else Path(__file__).resolve().parent / "logs" / "director.log"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = int(os.getenv("DIRECTOR_LOG_MAX_BYTES", "5242880"))
    backup_count = int(os.getenv("DIRECTOR_LOG_BACKUP_COUNT", "4"))

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
