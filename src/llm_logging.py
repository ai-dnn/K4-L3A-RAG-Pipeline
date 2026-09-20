"""Rotating JSONL logs; content is opt-in and credentials are redacted."""

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

LOG_PATH = Path(__file__).resolve().parents[1] / 'logs' / 'llm.log'
_lock = Lock()
_logger = logging.getLogger('rag.llm')
_logger.setLevel(logging.INFO)
_logger.propagate = False


def log_event(event: str, **fields) -> None:
    """Logging must never turn a successful model call into a failure."""
    try:
        with _lock:
            if not any(isinstance(handler, RotatingFileHandler) and
                       handler.baseFilename == str(LOG_PATH.resolve()) for handler in _logger.handlers):
                LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3, encoding='utf-8')
                handler.setFormatter(logging.Formatter('%(message)s'))
                _logger.addHandler(handler)
        record = {'time': datetime.now(timezone.utc).isoformat(), 'event': event, **fields}
        line = json.dumps(record, ensure_ascii=False)
        for name, value in os.environ.items():
            if value and any(part in name.upper() for part in ('API_KEY', 'TOKEN', 'SECRET', 'PASSWORD')):
                line = line.replace(json.dumps(value, ensure_ascii=False)[1:-1], '[REDACTED]')
        _logger.info(line)
    except Exception:
        logging.getLogger(__name__).warning('Unable to write LLM debug log')
