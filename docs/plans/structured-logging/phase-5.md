# Phase 5: Set Logging Context in `LinkedinSpider._initialize()`

> **Status:** pending
> **Depends on:** Phase 1, Phase 2

## Overview

Wire the session ID from `DriverManager` into the logging context so that `SpiderLoggerAdapter` (used by `log_action()`) includes `session_id` in every log record. This is a 2-line change in `core/scraper.py`.

## Implementation

**Files:**

- Modify: `src/linkedin_spider/core/scraper.py` -- add `set_logging_context()` call in `_initialize()`
- Test: `tests/test_logging.py` -- verify context is set after initialization

**What to test:**

- After `set_logging_context(session_id="test-123")`, a `SpiderLoggerAdapter` with no explicit `session_id` picks up `"test-123"` from context
- `get_logging_context()` returns `{"session_id": "test-123"}` after setting

**What to build:**

In `_initialize()`, after `self.driver_manager.setup_driver()` and before `self._initialize_scrapers()`:

```python
from linkedin_spider.core.logging import set_logging_context

# Set logging context for all scrapers
set_logging_context(session_id=self.driver_manager.session_id)
```

This ensures that when `_initialize_scrapers()` creates `BaseScraper` subclasses (which create `SpiderLoggerAdapter` instances in Phase 2), the context is already available.

**Commit:** `feat(logging): set session_id context from DriverManager during initialization`

## Done When

- [ ] `set_logging_context()` called in `_initialize()` with correct session_id
- [ ] Log records from `log_action()` include `session_id` field
- [ ] No constructor signature changes to `LinkedinSpider`, `BaseScraper`, or any scraper
- [ ] `make check` passes
