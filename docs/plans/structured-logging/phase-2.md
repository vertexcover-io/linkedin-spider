# Phase 2: Fix `BaseScraper.log_action()` Level Mapping and Wire Adapter

> **Status:** pending
> **Depends on:** Phase 1

## Overview

Fix the bug where `BaseScraper.log_action()` ignores its action parameter and always logs at INFO level. Replace the plain `logger.info()` call with a `SpiderLoggerAdapter` that maps the 5 action strings (`DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`) to correct Python log levels. `SUCCESS` maps to INFO since Python's logging has no SUCCESS level.

## Implementation

**Files:**

- Modify: `src/linkedin_spider/scrapers/base.py` -- add adapter, fix `log_action()`
- Test: `tests/test_logging.py` -- add tests for level mapping

**What to test:**

- `log_action("ERROR", "msg")` emits at ERROR level
- `log_action("WARNING", "msg")` emits at WARNING level
- `log_action("DEBUG", "msg")` emits at DEBUG level
- `log_action("INFO", "msg")` emits at INFO level
- `log_action("SUCCESS", "msg")` emits at INFO level
- `log_action("UNKNOWN_ACTION", "msg")` falls back to INFO level
- Log records from `log_action()` include `scraper` extra field set to the subclass name
- Log message format: `"[ClassName] ACTION: details"`

**What to build:**

In `scrapers/base.py`, add a `_ACTION_LEVELS` class-level dict mapping action strings to log levels. In `__init__`, create a `SpiderLoggerAdapter` wrapping the module logger with `{"scraper": self.__class__.__name__}`. Replace `log_action()` body:

```python
_ACTION_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "SUCCESS": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

def __init__(self, ...):
    # ... existing init ...
    self._logger = SpiderLoggerAdapter(
        logger, {"scraper": self.__class__.__name__}
    )

def log_action(self, action: str, details: str = "") -> None:
    """Log scraper action at the appropriate level."""
    level = self._ACTION_LEVELS.get(action.upper(), logging.INFO)
    self._logger.log(level, "[%s] %s: %s", self.__class__.__name__, action, details)
```

The import of `SpiderLoggerAdapter` comes from `linkedin_spider.core.logging`.

**Commit:** `fix(scrapers): map log_action() action parameter to correct log levels`

## Done When

- [ ] `log_action("ERROR", ...)` emits at ERROR level (not INFO)
- [ ] `log_action("WARNING", ...)` emits at WARNING level
- [ ] All 5 action strings map correctly
- [ ] Unknown actions default to INFO
- [ ] `scraper` context field appears in log records
- [ ] Existing `log_action()` call sites (102 calls across 5 files) work without changes
- [ ] `make check` passes
