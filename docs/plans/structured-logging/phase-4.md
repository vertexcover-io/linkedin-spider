# Phase 4: Wire Logging into MCP Server Entry Point

> **Status:** pending
> **Depends on:** Phase 1

## Overview

Replace the module-level `logging.basicConfig()` call in `mcp/server.py` with a `setup_logging()` call inside the `serve()` function. The MCP server reads `LOG_LEVEL`, `LOG_JSON`, and `LOG_FILE` environment variables. The `urllib3` silencing moves into `setup_logging()` (done in Phase 1), so the standalone line is removed.

## Implementation

**Files:**

- Modify: `src/linkedin_spider/mcp/server.py` -- remove `basicConfig` block, add `setup_logging()` in `serve()`

**What to test:**

- `serve()` calls `setup_logging()` before initializing the scraper (verified by checking handler configuration -- mock-based test)
- After removing `basicConfig`, the `linkedin_spider` logger still has correct handlers after `serve()` runs
- `urllib3.connectionpool` is still silenced

**What to build:**

Remove lines 15-20 from `mcp/server.py`:

```python
# REMOVE:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
```

In the `serve()` function, add at the top (before the first `logger.info` call):

```python
from linkedin_spider.core.logging import setup_logging

level = os.getenv("LOG_LEVEL", "INFO")
json_output = os.getenv("LOG_JSON", "").lower() in ("true", "1", "yes")
log_file = os.getenv("LOG_FILE")
setup_logging(level=level, json_output=json_output, log_file=log_file)
```

Note: The `logger = logging.getLogger(__name__)` line stays -- it's a child of the `linkedin_spider` namespace and will inherit the handlers set by `setup_logging()`.

**Commit:** `refactor(mcp): replace basicConfig with centralized setup_logging()`

## Done When

- [ ] `logging.basicConfig()` removed from module level
- [ ] `urllib3.connectionpool` silencing removed (handled by `setup_logging()`)
- [ ] `setup_logging()` called in `serve()` before scraper init
- [ ] Env vars `LOG_LEVEL`, `LOG_JSON`, `LOG_FILE` are respected
- [ ] MCP protocol on stdout is not affected (logs still go to stderr)
- [ ] `make check` passes
