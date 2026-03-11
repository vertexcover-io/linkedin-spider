# Plan: Structured Logging

> **Source:** `docs/plans/2026-03-11-structured-logging-design.md` > **Created:** 2026-03-11
> **Status:** planning

## Goal

Centralize logging configuration with JSON structured output support, fix `BaseScraper.log_action()` level mapping, and wire logging setup into CLI and MCP entry points with configurable flags and environment variables.

## Acceptance Criteria

- [ ] `setup_logging()` configures all `linkedin_spider.*` loggers from a single call
- [ ] JSON formatter produces one valid JSON object per log line with `timestamp`, `level`, `logger`, `message` fields
- [ ] `SpiderLoggerAdapter` injects `session_id` and `scraper` context into `log_action()` output
- [ ] `BaseScraper.log_action()` maps action strings to correct Python log levels (DEBUG/INFO/WARNING/ERROR)
- [ ] CLI accepts `--log-level`, `--log-json`, `--log-file` flags on every command
- [ ] Environment variables `LOG_LEVEL`, `LOG_JSON`, `LOG_FILE` provide defaults; CLI flags override
- [ ] MCP server uses `setup_logging()` instead of `logging.basicConfig()`
- [ ] `setup_logging()` is idempotent (no duplicate handlers on repeated calls)
- [ ] All new code passes `mypy --strict` and `make check`
- [ ] Unit tests cover formatter, adapter, setup, level mapping, env var fallback, idempotency

## Codebase Context

### Existing Patterns to Follow

- **Module-level loggers**: All 10 modules use `logging.getLogger(__name__)` -- this pattern is preserved, not replaced
- **CLI command parameters**: Each `@app.command` function in `cli/main.py` has its own parameter set (no shared dataclass pattern yet)
- **MCP server logging**: `mcp/server.py` lines 15-20 have `logging.basicConfig()` at module import time + `urllib3` silencing
- **Session ID**: Lives on `DriverManager.__init__(session_id="default")`, accessible via `self.driver_manager.session_id` on `LinkedinSpider`

### Test Infrastructure

- **Runner**: pytest with markers `slow`, `integration`
- **Existing tests**: `tests/conftest.py`, `tests/test_e2e.py`, `tests/test_mcp_server.py` -- all require `LINKEDIN_COOKIE`
- **Run command**: `make test` (or `uv run pytest`)
- **No existing unit tests** that run without credentials -- the new `test_logging.py` will be the first pure unit test file

### Key Files to Touch

- `src/linkedin_spider/core/logging.py` -- **new** (core module)
- `src/linkedin_spider/core/__init__.py` -- add export
- `src/linkedin_spider/__init__.py` -- add export
- `src/linkedin_spider/scrapers/base.py` -- fix `log_action()`, add adapter
- `src/linkedin_spider/cli/main.py` -- add log config params, call `setup_logging()`
- `src/linkedin_spider/mcp/server.py` -- replace `basicConfig` with `setup_logging()`
- `src/linkedin_spider/core/scraper.py` -- set logging context in `_initialize()`
- `tests/test_logging.py` -- **new** (unit tests)

## Phases

| #   | Phase                                                                                             | Status  | Depends On       |
| --- | ------------------------------------------------------------------------------------------------- | ------- | ---------------- |
| 1   | Core logging module (`setup_logging`, `JSONFormatter`, `SpiderLoggerAdapter`, context management) | pending | --               |
| 2   | Fix `BaseScraper.log_action()` level mapping and wire adapter                                     | pending | Phase 1          |
| 3   | Wire logging into CLI entry point with `--log-level`, `--log-json`, `--log-file` flags            | pending | Phase 1          |
| 4   | Wire logging into MCP server entry point with env var support                                     | pending | Phase 1          |
| 5   | Set logging context (`session_id`) in `LinkedinSpider._initialize()`                              | pending | Phase 1, Phase 2 |

## Phase Dependency Graph

```
Phase 1 (core logging module)
  |---> Phase 2 (fix log_action + adapter)
  |       \---> Phase 5 (set context in LinkedinSpider)
  |---> Phase 3 (CLI wiring)
  |---> Phase 4 (MCP wiring)
```

**Phases 2, 3, and 4 can run in parallel** -- they all depend only on Phase 1 and don't touch the same files. Phase 5 depends on both Phase 1 and Phase 2 (needs the adapter in BaseScraper before context is useful).
