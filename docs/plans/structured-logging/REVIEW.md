# Code Review: Structured Logging

**Date:** 2026-03-11
**Reviewer:** Claude Opus 4.6
**Plan:** `docs/plans/structured-logging/plan.md`
**Verdict:** APPROVE WITH SUGGESTIONS

---

## Summary

The implementation delivers all five phases of the structured logging plan. A new `core/logging.py` module centralizes configuration with JSON output support, `BaseScraper.log_action()` now maps action strings to correct Python log levels, CLI commands accept `--log-level`/`--log-json`/`--log-file` flags, the MCP server replaces `logging.basicConfig()` with `setup_logging_from_env()`, and `LinkedinSpider._initialize()` sets session context. All 69 unit tests pass. The new/changed files pass mypy clean (pre-existing mypy errors in `scraper.py` and `server.py` are unrelated to this change).

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| `setup_logging()` configures all `linkedin_spider.*` loggers from a single call | PASS |
| JSON formatter produces valid JSON with required fields | PASS |
| `SpiderLoggerAdapter` injects `session_id` and `scraper` context | PASS |
| `BaseScraper.log_action()` maps to correct log levels | PASS |
| CLI accepts `--log-level`, `--log-json`, `--log-file` flags | PASS |
| Env vars `LOG_LEVEL`, `LOG_JSON`, `LOG_FILE` provide defaults; CLI flags override | PASS |
| MCP server uses `setup_logging()` instead of `logging.basicConfig()` | PASS |
| `setup_logging()` is idempotent | PASS |
| All new code passes mypy --strict | PASS (new files only; pre-existing errors elsewhere) |
| Unit tests cover all specified areas | PASS (69 tests) |

---

## Critical Defects

None.

---

## Important Defects

### 1. Module-level `_logging_context` is a global mutable singleton -- thread safety concern

**File:** `src/linkedin_spider/core/logging.py`, line 13

The `_logging_context` dict is shared across threads with no synchronization. If `LinkedinSpider` is ever used from multiple threads (or if the MCP server processes concurrent requests), `set_logging_context()` and the read in `SpiderLoggerAdapter.process()` could race. This is unlikely to cause crashes (dict operations in CPython are GIL-protected), but could produce incorrect `session_id` values in log records.

**Suggestion:** Consider using `contextvars.ContextVar` instead of a plain dict, or document that `set_logging_context` is not thread-safe.

### 2. `setup_logging()` clears handlers on every call, which could drop handlers added by third-party code or test fixtures

**File:** `src/linkedin_spider/core/logging.py`, line 139

`logger.handlers.clear()` is the idempotency mechanism, but if any external code (e.g., a monitoring library or pytest's caplog) has attached a handler to the `linkedin_spider` namespace logger, calling `setup_logging()` will silently remove it. The plan explicitly requires idempotency and the current approach is pragmatic, but this side effect should be documented in the docstring.

---

## Suggestions (non-blocking)

### S1. FileHandler leak in `setup_logging()` on repeated calls

When `setup_logging()` is called multiple times with `log_file` set, `logger.handlers.clear()` removes old FileHandler references but does not call `.close()` on them first. This leaves file descriptors open until GC. Consider closing handlers before clearing:

```python
for handler in logger.handlers:
    handler.close()
logger.handlers.clear()
```

### S2. `_logging_context` is exported from tests via private import

**File:** `tests/test_logging.py`, line 16

Tests import the private `_logging_context` dict directly to clear it in the fixture. This creates tight coupling to the internal representation. Consider adding a `clear_logging_context()` function to the public API (or at least a `_reset_logging_context()` test helper).

### S3. MCP `serve()` does not forward any log configuration flags

**File:** `src/linkedin_spider/mcp/server.py`, line 306

The CLI `serve` command calls `setup_logging_from_env()` with no arguments, meaning it relies entirely on env vars. The plan says "Environment variables `LOG_LEVEL`, `LOG_JSON`, `LOG_FILE` provide defaults" which is satisfied, but the CLI command could also accept `--log-level` etc. flags for consistency with the main CLI. This is a nice-to-have, not a plan requirement.

### S4. Plan status not updated

All phase statuses in `plan.md` and the individual phase files still say "pending". Consider updating them to "done" since the implementation is complete.

### S5. Text formatter format string differs from the old MCP basicConfig format

The old MCP server used `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` and the new `setup_logging()` uses the same format, so this is consistent. Good.

### S6. Consider adding `exc_info` / `stack_info` to JSONFormatter

The JSON formatter currently only emits `timestamp`, `level`, `logger`, `message`, and the three context fields. If an exception is logged (e.g., `logger.exception(...)`), the traceback will not appear in JSON output. Consider adding `exc_info` to the JSON dict when present on the record.

---

## Test Coverage Assessment

The 69 tests are thorough and well-structured:

- **TestSetupLogging** (15 tests): level setting, idempotency, file handlers, urllib3 silencing
- **TestJSONFormatter** (6 tests): JSON validity, required fields, extras, non-serializable handling
- **TestSpiderLoggerAdapter** (5 tests): injection, override priority, module context fallback
- **TestLoggingContext** (4 tests): set/get roundtrip, copy semantics
- **TestBaseScraperLogAction** (9 tests): all level mappings, message format, context injection
- **TestLogConfig / TestConfigureLogging** (13 tests): CLI dataclass, env var fallback, override priority
- **TestLinkedinSpiderSetsLoggingContext** (3 tests): session_id propagation, call ordering
- **TestMcpServerLoggingWiring** (6 tests): no basicConfig, import verification, serve() delegation
- **TestSetupLoggingFromEnvIntegration** (8 tests): end-to-end env var flow

Missing edge case: no test verifies that `setup_logging(log_file=...)` actually writes log output to the file (only that the handler is attached).

---

## Files Reviewed

- `src/linkedin_spider/core/logging.py` (new, 169 lines)
- `src/linkedin_spider/core/__init__.py` (modified)
- `src/linkedin_spider/__init__.py` (modified)
- `src/linkedin_spider/scrapers/base.py` (modified)
- `src/linkedin_spider/cli/main.py` (modified)
- `src/linkedin_spider/mcp/server.py` (modified)
- `src/linkedin_spider/core/scraper.py` (modified)
- `tests/test_logging.py` (new, 617 lines)
- `tests/test_mcp_logging.py` (new, 186 lines)
