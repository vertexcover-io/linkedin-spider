# Logging

## Gotchas

### log_action() action strings are a closed set

Despite the free-form string parameter, only 5 values are used across all 102 call sites: `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`. No domain-specific actions (NAVIGATE, SCRAPE, etc.) exist. Verified by grepping all scraper files.

### MCP server's logging.basicConfig runs at import time

`mcp/server.py` line 15 calls `logging.basicConfig(...)` at module level. Any replacement `setup_logging()` must remove this line entirely -- calling `setup_logging()` later won't override it because `basicConfig` is a no-op when the root logger already has handlers.

### session_id is not threaded to scrapers

`DriverManager` holds `session_id` (default `"default"`), but `LinkedinSpider._initialize_scrapers()` passes only `(driver, wait, human_behavior, tracking_handler)` to each scraper. A module-level context variable is the pragmatic solution since the codebase enforces single-instance per process (MCP uses a global `_scraper_instance`).

## Patterns

### Cyclopts shared parameters via dataclass

Cyclopts supports global CLI parameters across commands using a common dataclass decorated with `@Parameter(name="*")` to flatten the namespace. This avoids duplicating `--log-level`, `--log-json`, `--log-file` on every command function.

### No pure unit tests exist yet

All existing tests (`test_e2e.py`, `test_mcp_server.py`) require `LINKEDIN_COOKIE` and skip without it. `tests/test_logging.py` is the first test file that runs without credentials, making it the template for future unit tests.

## Decisions

### Configure namespace logger, not root

Chose `logging.getLogger("linkedin_spider")` over root logger because it avoids interfering with selenium/urllib3/fastmcp logging. Child loggers via `getLogger(__name__)` inherit the config automatically. Trade-off: `urllib3.connectionpool` silencing must be done separately.
