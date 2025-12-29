"""
Simple centralized logger for backend.
- Writes to stdout and rotating file ./logs/app.log
- Single initialization, reusable via get_logger(name)
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def _ensure_log_dir():
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass


def _build_handler():
    _ensure_log_dir()
    handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    return handler


def _build_stream_handler():
    return logging.StreamHandler()


def _configure_root():
    if getattr(_configure_root, "_configured", False):
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers = []
    file_handler = _build_handler()
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    stream_handler = _build_stream_handler()
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    logging.basicConfig(level=logging.INFO, handlers=handlers)
    _configure_root._configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(name)

