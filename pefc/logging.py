from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Thread-local storage for context
_context = threading.local()


def init_logging(
    level: str = "INFO",
    json_mode: bool = False,
    context: Optional[Dict[str, Any]] = None,
    gha_annotations: bool = False,
) -> None:
    """
    Initialize logging with structured output.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_mode: If True, output JSON logs; if False, human-readable text
        context: Initial context to set
        gha_annotations: If True, emit GitHub Actions annotations for warnings/errors
    """
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set level
    try:
        log_level = getattr(logging, level.upper())
    except AttributeError:
        log_level = logging.INFO  # Default to INFO for invalid levels
    root_logger.setLevel(log_level)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Choose formatter
    if json_mode:
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)

    # Add filters
    handler.addFilter(ContextFilter())
    handler.addFilter(TruncFilter())

    # Add GitHub Actions handler if requested
    if gha_annotations and os.getenv("GITHUB_ACTIONS"):
        handler.addFilter(GHAFilter())

    root_logger.addHandler(handler)

    # Set initial context
    if context:
        set_context(**context)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def set_context(**kwargs: Any) -> None:
    """Set logging context."""
    if not hasattr(_context, "data"):
        _context.data = {}
    _context.data.update(kwargs)


def update_context(**kwargs: Any) -> None:
    """Update logging context (merge with existing)."""
    if not hasattr(_context, "data"):
        _context.data = {}
    _context.data.update(kwargs)


def clear_context() -> None:
    """Clear logging context."""
    _context.data = {}


def get_context() -> Dict[str, Any]:
    """Get current logging context."""
    return getattr(_context, "data", {})


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "pid": os.getpid(),
            "thread": threading.current_thread().name,
        }

        # Add event if present
        if hasattr(record, "event"):
            entry["event"] = record.event

        # Add context
        context = get_context()
        if context:
            entry["context"] = context

        # Add extra fields
        if hasattr(record, "kv") and record.kv:
            entry["kv"] = redact_kv(record.kv)

        # Add exception info
        if record.exc_info:
            entry["err"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stack": (self.formatException(record.exc_info) if record.exc_info else None),
            }

        return json.dumps(entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def __init__(self):
        super().__init__("%(levelname)s %(name)s — %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        # Add context to message if present
        context = get_context()
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            record.msg = f"{record.msg} [{context_str}]"

        return super().format(record)


class ContextFilter(logging.Filter):
    """Filter that injects context into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = get_context()
        if context:
            record.context = context
        return True


class TruncFilter(logging.Filter):
    """Filter that truncates long messages and extra fields."""

    def __init__(self, max_msg_length: int = 1000, max_kv_length: int = 500):
        super().__init__()
        self.max_msg_length = max_msg_length
        self.max_kv_length = max_kv_length

    def filter(self, record: logging.LogRecord) -> bool:
        # Truncate message
        if len(record.getMessage()) > self.max_msg_length:
            record.msg = record.getMessage()[: self.max_msg_length] + "..."

        # Truncate kv fields
        if hasattr(record, "kv") and record.kv:
            for key, value in record.kv.items():
                if isinstance(value, str) and len(value) > self.max_kv_length:
                    record.kv[key] = value[: self.max_kv_length] + "..."

        return True


class GHAFilter(logging.Filter):
    """Filter that emits GitHub Actions annotations for warnings/errors."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            print(f"::error::{record.getMessage()}", file=sys.stderr)
        elif record.levelno >= logging.WARNING:
            print(f"::warning::{record.getMessage()}", file=sys.stderr)

        return True


def redact_kv(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive keys in a dictionary."""
    sensitive_keys = {
        "token",
        "secret",
        "password",
        "api_key",
        "bearer",
        "authorization",
        "key",
        "credential",
        "private",
        "sensitive",
    }

    redacted = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            redacted[key] = "***"
        elif isinstance(value, dict):
            redacted[key] = redact_kv(value)
        elif isinstance(value, str) and len(value) > 100:
            # Truncate long strings
            redacted[key] = value[:100] + "..." if len(value) > 100 else value
        else:
            redacted[key] = value

    return redacted


@contextmanager
def timed(step: str, logger: Optional[logging.Logger] = None):
    """Context manager for timing operations."""
    if logger is None:
        logger = get_logger(__name__)

    start_time = time.time()
    logger.info(f"Starting {step}", extra={"event": "timer.start", "step": step})

    try:
        yield
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Completed {step}",
            extra={"event": "timer.complete", "step": step, "elapsed_ms": elapsed_ms},
        )


def setup_logging_from_config(config) -> None:
    """Setup logging from configuration object."""
    # Check for environment overrides
    level = os.getenv("PEFC_LOG_LEVEL", config.logging.level)
    json_mode = os.getenv("PEFC_LOG_JSON", "").lower() in ("1", "true", "yes")
    if not json_mode:
        json_mode = config.logging.json_mode

    # Check for GitHub Actions
    gha_annotations = os.getenv("GITHUB_ACTIONS") is not None

    init_logging(level=level, json_mode=json_mode, gha_annotations=gha_annotations)
