# Phase 1: Core Logging Module

> **Status:** pending
> **Depends on:** none

## Overview

Create `src/linkedin_spider/core/logging.py` with all the logging infrastructure: `setup_logging()` for centralized configuration, `JSONFormatter` for structured output, `SpiderLoggerAdapter` for injecting context fields, and module-level context management functions. After this phase, other phases can import and use these components. Export `setup_logging` from `core/__init__.py` and the top-level `__init__.py`.

## Implementation

**Files:**

- Create: `src/linkedin_spider/core/logging.py`
- Modify: `src/linkedin_spider/core/__init__.py` -- add `setup_logging` to imports and `__all__`
- Modify: `src/linkedin_spider/__init__.py` -- add `setup_logging` to imports and `__all__`
- Test: `tests/test_logging.py`

**What to test:**

- `setup_logging()` configures the `linkedin_spider` namespace logger with a StreamHandler on stderr
- `setup_logging(json_output=True)` attaches `JSONFormatter`; output is valid JSON with `timestamp`, `level`, `logger`, `message` keys
- `setup_logging(log_file="/tmp/test.log")` adds a FileHandler; creates parent directories
- `setup_logging(level="DEBUG")` sets logger to DEBUG level
- `setup_logging(level="INVALID")` falls back to INFO and emits a warning (does not raise)
- Idempotency: calling `setup_logging()` twice does not duplicate handlers
- `JSONFormatter` handles non-serializable extras via `default=str`
- `SpiderLoggerAdapter` injects `session_id` and `scraper` into log record extras
- `set_logging_context(session_id="abc")` / `get_logging_context()` round-trips correctly
- `SpiderLoggerAdapter` reads `session_id` from module-level context when not set directly
- `urllib3.connectionpool` logger is silenced at ERROR level (unless level is DEBUG)

**What to build:**

```python
"""Structured logging configuration for linkedin-spider."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Module-level context for session information
_logging_context: dict[str, str] = {}

NAMESPACE = "linkedin_spider"


def set_logging_context(**kwargs: str) -> None:
    """Set module-level logging context (e.g., session_id)."""
    _logging_context.update(kwargs)


def get_logging_context() -> dict[str, str]:
    """Get current logging context."""
    return dict(_logging_context)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include extra context fields if present
        for key in ("session_id", "scraper", "target_url"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value
        return json.dumps(log_entry, default=str)


class SpiderLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that injects spider context into log records."""

    def process(
        self, msg: str, kwargs: Any
    ) -> tuple[str, Any]:
        extra = kwargs.get("extra", {})
        # Merge adapter's extra with call-site extra
        combined = {**self.extra, **extra}
        # Pull session_id from module context if not set
        if "session_id" not in combined or combined["session_id"] is None:
            combined["session_id"] = _logging_context.get(
                "session_id", "unknown"
            )
        kwargs["extra"] = combined
        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure logging for the linkedin_spider namespace.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
            Invalid values fall back to INFO.
        json_output: If True, use JSON formatter.
        log_file: Optional file path for log output.

    Returns:
        The configured namespace logger.
    """
    logger = logging.getLogger(NAMESPACE)

    # Validate level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        # Use stderr directly to avoid chicken-and-egg with logger config
        sys.stderr.write(
            f"WARNING: Invalid log level '{level}', falling back to INFO\n"
        )

    logger.setLevel(numeric_level)

    # Clear existing handlers (idempotency)
    logger.handlers.clear()

    # Choose formatter
    if json_output:
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # stderr handler (always present)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # Optional file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Silence noisy third-party loggers
    # (but allow them through if user explicitly asks for DEBUG)
    if numeric_level > logging.DEBUG:
        logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

    # Prevent propagation to root logger (avoid duplicate output)
    logger.propagate = False

    return logger
```

**Commit:** `feat(logging): add core logging module with JSON formatter and context adapter`

## Done When

- [ ] `setup_logging()` returns configured logger with correct level and handlers
- [ ] JSON output is valid JSON with required fields
- [ ] Idempotency: no duplicate handlers
- [ ] Invalid level falls back to INFO
- [ ] File handler creates parent dirs
- [ ] `SpiderLoggerAdapter` injects context fields
- [ ] `setup_logging` is importable from `linkedin_spider` and `linkedin_spider.core`
- [ ] All tests pass, `make check` passes
