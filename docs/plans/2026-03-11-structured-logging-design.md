# Structured Logging -- Design

## Problem Statement

Logging across linkedin-spider is inconsistent and limited in three concrete ways:

1. **No centralized configuration.** The MCP server calls `logging.basicConfig()` at module level; the CLI configures nothing. This means CLI users get Python's default WARNING-only output with no control.
2. **`BaseScraper.log_action()` ignores its own action parameter.** All 102 calls across 5 scraper files -- including 26 "ERROR" calls and 7 "WARNING" calls -- emit at INFO level regardless.
3. **No structured output.** All messages are free-form strings, making it impossible to feed logs into aggregation tools or programmatically filter by scraper, session, or target URL.

## Context

### Current logging landscape

- **10 modules** use `logging.getLogger(__name__)` -- this is the standard pattern and should be preserved.
- **`log_action()` action strings** are limited to exactly 5 values: `"DEBUG"`, `"INFO"`, `"SUCCESS"`, `"WARNING"`, `"ERROR"`. No domain-specific action strings (like "NAVIGATE" or "SCRAPE") exist despite what one might expect.
- **MCP server** has `logging.basicConfig(level=INFO, format=..., stream=stderr)` at module import time (line 15-18 of `mcp/server.py`). It also silences `urllib3.connectionpool` at ERROR level.
- **CLI** (`cli/main.py`) has zero logging configuration. The entry point in `cli/__main__.py` is a thin wrapper that imports and calls `app()`.
- **Session ID** lives on `DriverManager` (default `"default"`) but is never passed through to scrapers. `LinkedinSpider` creates `DriverManager` and then passes `(driver, wait, human_behavior, tracking_handler)` to each scraper's `__init__`.
- **Mypy strict mode** is enforced (`disallow_untyped_defs=true`). Every function signature needs full type annotations.
- **Python 3.10+** is the target. `str | None` union syntax is used throughout.
- **No new dependencies allowed.** Everything must use stdlib `logging` and `json`.

### What triggered this

The spec at `docs/specs/structured-logging.md` provides a detailed design. This document validates that spec against reality and resolves the architectural decisions the spec leaves implicit.

## Requirements

### Functional Requirements

1. **FR1:** A single `setup_logging()` function configures all `linkedin_spider.*` loggers.
2. **FR2:** JSON-structured output mode produces one valid JSON object per log line.
3. **FR3:** `BaseScraper.log_action()` maps its action parameter to the correct Python log level.
4. **FR4:** CLI accepts `--log-level`, `--log-json`, and `--log-file` flags on every command.
5. **FR5:** Environment variables `LOG_LEVEL`, `LOG_JSON`, `LOG_FILE` provide defaults; CLI flags override them.
6. **FR6:** MCP server replaces its `logging.basicConfig()` with `setup_logging()`, reading env vars.
7. **FR7:** JSON log records include: `timestamp`, `level`, `logger`, `message`. Contextual fields (`session_id`, `scraper`, `target_url`) are included when available.

### Non-Functional Requirements

1. **NFR1:** No new runtime dependencies.
2. **NFR2:** All new code passes `mypy --strict` (type annotations on every def).
3. **NFR3:** Existing `logging.getLogger(__name__)` usage in 10 modules continues to work without changes.
4. **NFR4:** No public API changes -- `LinkedinSpider`, `ScraperConfig`, `BaseScraper` constructors keep the same signatures.
5. **NFR5:** Log configuration is idempotent -- calling `setup_logging()` twice doesn't duplicate handlers.

### Edge Cases and Boundary Conditions

1. **EC1: `setup_logging()` called twice.** Must not add duplicate handlers. Use `logger.handlers` check or `removeHandler` before adding.
2. **EC2: Invalid log level string.** Fall back to INFO with a warning, don't crash.
3. **EC3: Log file path with missing parent directories.** Create parent dirs or fail gracefully.
4. **EC4: JSON serialization of non-serializable extras.** Use a safe `default=str` in `json.dumps()`.
5. **EC5: MCP stdio transport.** Logs go to stderr. JSON log output on stderr must not interfere with MCP protocol on stdout. This already works because the existing `basicConfig` uses `stream=sys.stderr`.
6. **EC6: `log_action()` called with unexpected action string.** Default to INFO level (the spec handles this).
7. **EC7: `SpiderLoggerAdapter` used before context is set.** Fields should default to sensible values (e.g., `"unknown"` for session_id).

## Key Insights

### 1. Session ID threading is the hardest part -- and can be deferred

The spec mentions attaching `session_id` to log records. Currently, `session_id` lives on `DriverManager` and is never passed to scrapers. Threading it through would require changing `BaseScraper.__init__` or `LinkedinSpider._initialize_scrapers()`.

**Decision:** Use a module-level context variable in `core/logging.py` that gets set once during `LinkedinSpider._initialize()`. The `SpiderLoggerAdapter` reads from this context. This avoids constructor signature changes (NFR4) and works because there's only ever one `LinkedinSpider` instance per process.

### 2. `SpiderLoggerAdapter` should be opt-in, not forced

The spec suggests each scraper gets an adapter. But 10 modules already use `logging.getLogger(__name__)` with direct `logger.info()` / `logger.debug()` calls (not through `log_action()`). Changing all of those to use an adapter would be a large, invasive change.

**Decision:** Only `BaseScraper` uses `SpiderLoggerAdapter` for its `log_action()` method. The 10 existing module-level loggers continue to use plain `getLogger(__name__)`. They still benefit from the centralized handler configuration (JSON format, file output, level control). Context fields (session_id, etc.) appear in `log_action()` output but not in direct `logger.debug()` calls -- and that's fine for v1.

### 3. Cyclopts global parameters need a specific pattern

Cyclopts supports shared parameters across commands via a common dataclass with `@Parameter(name="*")` to flatten the namespace. This is the cleanest way to add `--log-level`, `--log-json`, `--log-file` to every CLI command without duplicating parameters on each function.

However, examining the current CLI structure: each command is an independent `@app.command` function with its own parameter set. There is no meta-app or shared dataclass pattern in use.

**Decision:** Add a `LogConfig` dataclass with the three logging parameters and add it as a parameter to each command function. This is slightly repetitive but consistent with the existing pattern, avoids introducing meta-app complexity, and is easy to understand.

### 4. MCP server's module-level `logging.basicConfig` is a timing hazard

The current `logging.basicConfig(...)` runs at module import time (top of `mcp/server.py`). If `setup_logging()` is called later (in `serve()`), it needs to undo what `basicConfig` did. Since `basicConfig` is a no-op if the root logger already has handlers, and we're configuring the `linkedin_spider` logger (not root), this actually works -- but only if we remove the existing `basicConfig` call entirely.

**Decision:** Remove the `logging.basicConfig(...)` block from `mcp/server.py` and replace it with a `setup_logging()` call inside the `serve()` function, before scraper initialization. The `urllib3` silencing stays but moves into `setup_logging()`.

## Architectural Challenges

### Challenge 1: Configuring a namespace logger vs. root logger

The spec correctly says to configure the `linkedin_spider` logger, not root. This means `logging.getLogger("linkedin_spider")` gets the handlers, and all child loggers (via `getLogger(__name__)`) inherit them. This is the right approach because it doesn't interfere with third-party library logging (selenium, urllib3, fastmcp).

However, the `urllib3.connectionpool` silencing currently works because `basicConfig` configures the root logger. When we switch to namespace logger, we need to ensure `urllib3` noise is still suppressed. Solution: keep the `logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)` call in `setup_logging()`.

### Challenge 2: Handler idempotency

If `setup_logging()` is called multiple times (e.g., tests, or re-initialization), handlers must not accumulate. Solution: clear existing handlers on the `linkedin_spider` logger before adding new ones.

### Challenge 3: `log_action()` backward compatibility

Currently `log_action("ERROR", "something failed")` emits at INFO. After the fix, it emits at ERROR. This is a behavior change, but it's a _bug fix_ -- the current behavior is clearly wrong. Code that calls `log_action("ERROR", ...)` expects error-level semantics. No backward compatibility concern here.

## Approaches Considered

### Approach A: Minimal -- Fix levels + centralize config only

Just fix `log_action()` level mapping and create `setup_logging()` with human-readable format. No JSON, no adapter, no context fields. Wire into CLI and MCP.

- Pro: Smallest change, lowest risk.
- Con: Doesn't address structured output or context fields. Misses half the spec's goals.

### Approach B: Full spec implementation with constructor changes

Implement everything in the spec, including passing session_id through constructors and converting all 10 modules to use `SpiderLoggerAdapter`.

- Pro: Most complete context in every log line.
- Con: Invasive changes to `BaseScraper.__init__`, every scraper constructor, and all 10 module-level logger usages. High risk of breaking things. Violates NFR4 (no public API changes).

### Approach C: Pragmatic middle -- centralize + JSON + adapter for log_action only

Create `setup_logging()` with JSON support. Use `SpiderLoggerAdapter` only in `BaseScraper.log_action()`. Use a module-level context variable for session_id. Leave existing `getLogger(__name__)` calls untouched.

- Pro: Hits all spec goals. Minimal invasion. Existing loggers benefit from centralized config automatically.
- Con: Context fields only appear in `log_action()` output, not in direct `logger.debug()` calls from individual modules.

## Chosen Approach

**Approach C: Pragmatic middle.**

The context field gap (direct `logger.debug()` calls lacking session_id) is acceptable because:

- Those are low-level debug messages (DOM extraction failures, scroll issues).
- They already include the module name via `%(name)s` / the `logger` JSON field.
- Adding context to them can be done in a follow-up by converting module loggers to adapters one at a time.

## High-Level Design

### Component overview

```
setup_logging()                    <-- called once by CLI or MCP entry point
    |
    v
linkedin_spider logger             <-- namespace logger, gets handlers
    |                                  (stderr StreamHandler, optional FileHandler)
    |--- formatters
    |       |--- HumanFormatter     <-- default: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    |       |--- JSONFormatter      <-- opt-in: single-line JSON per record
    |
    v
child loggers (getLogger(__name__))  <-- inherit handlers from namespace logger
    |--- linkedin_spider.core.driver
    |--- linkedin_spider.core.auth
    |--- linkedin_spider.scrapers.profile
    |--- ... (10 total)
    |
    v
SpiderLoggerAdapter                <-- wraps logger in BaseScraper only
    |--- injects: session_id, scraper class name
    |--- used by: log_action()
```

### Data flow

1. Entry point (CLI or MCP) calls `setup_logging(level, json_output, log_file)`.
2. `setup_logging()` configures the `linkedin_spider` namespace logger with appropriate handlers and formatter.
3. `LinkedinSpider._initialize()` sets the module-level logging context (session_id).
4. Each `BaseScraper` subclass gets a `SpiderLoggerAdapter` wrapping its module logger, populated with scraper class name and reading session_id from context.
5. `log_action()` uses the adapter, mapping action strings to log levels.
6. Direct `logger.info()` calls in modules use plain loggers but inherit the centralized handler config.

### Configuration precedence

```
CLI flag  >  Environment variable  >  Default value
```

For MCP server (no CLI flags on tool invocation):

```
serve() CLI flag  >  Environment variable  >  Default value
```

### File change summary

| File                                   | Nature of change                                                                                                                     |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `src/linkedin_spider/core/logging.py`  | **New.** ~80-100 lines. `setup_logging()`, `JSONFormatter`, `SpiderLoggerAdapter`, `set_logging_context()`, `get_logging_context()`. |
| `src/linkedin_spider/core/__init__.py` | Add `setup_logging` to exports.                                                                                                      |
| `src/linkedin_spider/scrapers/base.py` | Replace `log_action()` body with level-mapped adapter call. Add `SpiderLoggerAdapter` as `self._logger`. ~15 lines changed.          |
| `src/linkedin_spider/cli/main.py`      | Add `LogConfig` dataclass, add to each command, call `setup_logging()`. ~20 lines added.                                             |
| `src/linkedin_spider/mcp/server.py`    | Remove `logging.basicConfig` block, add `setup_logging()` call in `serve()` reading env vars. ~10 lines changed.                     |
| `src/linkedin_spider/core/scraper.py`  | Add `set_logging_context(session_id=...)` call in `_initialize()`. 2 lines added.                                                    |
| `tests/test_logging.py`                | **New.** Unit tests for formatter, adapter, setup, level mapping, env var fallback, idempotency.                                     |

## Open Questions

1. **Should `LOG_JSON` env var also affect the MCP `serve()` CLI flags?** The spec says CLI flags override env vars, which is standard. But the MCP `serve()` command has its own CLI flags. Recommendation: yes, same precedence rules apply everywhere.

2. **Should the human-readable format change?** The current MCP format is `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. The spec doesn't propose changing it. Recommendation: keep it as-is for backward compatibility.

3. **Should `urllib3` silencing move into `setup_logging()` or stay separate?** Recommendation: move it into `setup_logging()` so all logging config is in one place, but only apply it if the caller doesn't explicitly set DEBUG level (so `--log-level DEBUG` can reveal urllib3 noise if needed).

## Risks and Mitigations

| Risk                                                                        | Likelihood | Impact   | Mitigation                                                                                                                                                                                                                            |
| --------------------------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `log_action()` level change surfaces hidden errors in log output            | Medium     | Low      | This is the desired behavior. Users may see ERROR lines they didn't see before, which is informative not harmful.                                                                                                                     |
| Removing `logging.basicConfig` from MCP server breaks early startup logging | Low        | Medium   | `setup_logging()` is called in `serve()` before `_initialize_scraper()`. Any import-time log calls happen before config, but these would go to stderr via Python's default lastResort handler at WARNING+ level, which is acceptable. |
| Cyclopts `LogConfig` dataclass integration doesn't work as expected         | Low        | Medium   | The pattern is documented and used in cyclopts ecosystem. Test early with a single command before wiring all five.                                                                                                                    |
| JSON formatter performance overhead on high-volume debug logging            | Very Low   | Very Low | `json.dumps()` on a small dict is negligible. Log volume is inherently low (human-speed scraping).                                                                                                                                    |

## Assumptions

1. **Single `LinkedinSpider` instance per process.** Module-level logging context works because only one session_id is active. If multi-instance support is ever needed, this would need to move to contextvars or thread-local storage. The current codebase reinforces this assumption (MCP server uses a global `_scraper_instance`).

2. **Python 3.10+ is the floor.** Union type syntax `str | None` is used. No need for `from __future__ import annotations`.

3. **cyclopts >= 2.0 supports the dataclass parameter pattern.** The `pyproject.toml` specifies `cyclopts>=2.0.0`.

4. **Stderr is the correct output stream for logs in both CLI and MCP modes.** CLI data output goes to stdout (JSON/CSV results); MCP protocol uses stdout for messages. Logs on stderr don't interfere with either.

5. **No existing tests depend on specific log output.** The existing test files (`test_e2e.py`, `test_mcp_server.py`) are integration tests that require `LINKEDIN_COOKIE`; they don't assert on log content.
