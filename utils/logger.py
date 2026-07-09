from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = "%(asctime)s  [%(levelname)-8s]  %(name)s.%(funcName)s:%(lineno)d  %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_root = logging.getLogger("meta_mcp")
_root.setLevel(logging.DEBUG)

_file_handler = RotatingFileHandler(
    str(LOG_DIR / "app.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
_root.addHandler(_file_handler)

_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
_root.addHandler(_console_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"meta_mcp.{name}")


logger = get_logger("root")
