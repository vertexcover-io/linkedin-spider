"""Structured logging configuration for linkedin-spider."""

import json
import logging
import os
import sys
from collections.abc import MutableMapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Module-level context for session information
_logging_context: dict[str, str] = {}

NAMESPACE = "linkedin_spider"

_TRUTHY_VALUES = frozenset({"true", "1", "yes"})


def _parse_bool_env(env_var: str) -> bool:
    """Parse a boolean environment variable (true/1/yes are truthy)."""
    return os.getenv(env_var, "").lower() in _TRUTHY_VALUES


def setup_logging_from_env(
    *,
    level: str | None = None,
    json_output: bool | None = None,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure logging from explicit values with env var fallback.

    Each parameter, when ``None``, falls back to the corresponding
    environment variable (``LOG_LEVEL``, ``LOG_JSON``, ``LOG_FILE``).
    This is the single entry point used by both the CLI and MCP server.
    """
    resolved_level = level if level is not None else os.getenv("LOG_LEVEL", "INFO")
    resolved_json = json_output if json_output is not None else _parse_bool_env("LOG_JSON")
    resolved_file = log_file or os.getenv("LOG_FILE") or None
    return setup_logging(
        level=resolved_level,
        json_output=resolved_json,
        log_file=resolved_file,
    )


def set_logging_context(**kwargs: str) -> None:
    """Set module-level logging context (e.g., session_id)."""
    _logging_context.update(kwargs)


def get_logging_context() -> dict[str, str]:
    """Get current logging context (returns a copy)."""
    return dict(_logging_context)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Output contains timestamp, level, logger, message, and any
        extra context fields (session_id, scraper, target_url) if present.
        Non-serializable values are coerced to strings via default=str.
        """
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
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


class SpiderLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Logger adapter that injects spider context into log records.

    Merges adapter-level extra with call-site extra, and falls back
    to module-level context for session_id when not explicitly set.
    """

    def process(
        self,
        msg: str,
        kwargs: MutableMapping[str, Any],
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Inject context fields into the log record's extra dict."""
        raw_extra = kwargs.get("extra")
        extra: dict[str, Any] = dict(raw_extra) if raw_extra is not None else {}
        # Merge adapter's extra with call-site extra (call-site wins)
        merged_base: dict[str, Any] = dict(self.extra) if self.extra else {}
        combined: dict[str, Any] = {**merged_base, **extra}
        # Pull session_id from module context if not set
        if "session_id" not in combined or combined["session_id"] is None:
            combined["session_id"] = _logging_context.get("session_id", "unknown")
        kwargs["extra"] = combined
        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: str | None = None,
) -> logging.Logger:
    """Configure logging for the linkedin_spider namespace.

    Configures the root ``linkedin_spider`` logger with a stderr
    StreamHandler and, optionally, a FileHandler.  Calling this function
    multiple times is safe -- existing handlers are cleared first.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
            Invalid values fall back to INFO with a warning on stderr.
        json_output: If True, use JSONFormatter for structured output.
        log_file: Optional file path for log output.  Parent directories
            are created automatically.

    Returns:
        The configured namespace logger.
    """
    logger = logging.getLogger(NAMESPACE)

    # Validate level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        # Use stderr directly to avoid chicken-and-egg with logger config
        sys.stderr.write(f"WARNING: Invalid log level '{level}', falling back to INFO\n")

    logger.setLevel(numeric_level)

    # Clear existing handlers (idempotency)
    logger.handlers.clear()

    # Choose formatter
    formatter: logging.Formatter
    if json_output:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # stderr handler (always present)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # Optional file handler
    if log_file is not None:
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
