# Phase 3: Wire Logging into CLI Entry Point

> **Status:** pending
> **Depends on:** Phase 1

## Overview

Add `--log-level`, `--log-json`, and `--log-file` flags to every CLI command in `cli/main.py`. These flags override environment variables `LOG_LEVEL`, `LOG_JSON`, `LOG_FILE`. Each command calls `setup_logging()` before creating the scraper. Uses a `LogConfig` dataclass to avoid repeating the three parameters on every command function.

## Implementation

**Files:**

- Modify: `src/linkedin_spider/cli/main.py` -- add `LogConfig`, add to each command, call `setup_logging()`
- Test: `tests/test_logging.py` -- add tests for env var fallback and CLI override

**What to test:**

- `LogConfig` resolves `log_level` from explicit value over `LOG_LEVEL` env var over default `"INFO"`
- `LogConfig` resolves `log_json` from explicit value over `LOG_JSON` env var (truthy: `"true"`, `"1"`, `"yes"`)
- `LogConfig` resolves `log_file` from explicit value over `LOG_FILE` env var
- `setup_logging()` is called with resolved values (mock test -- don't need real scraper)

**What to build:**

Add a `LogConfig` dataclass with the three log parameters. Add it as a parameter to each of the 5 command functions (`search`, `profile`, `company`, `connections`, `search_posts`). Each command calls `_configure_logging(log_config)` at the top of its `try` block.

```python
from dataclasses import dataclass

from linkedin_spider.core.logging import setup_logging


@dataclass
class LogConfig:
    """Shared logging configuration for CLI commands."""
    log_level: Annotated[
        str | None,
        Parameter(name=["--log-level"], help="Log level (DEBUG, INFO, WARNING, ERROR)"),
    ] = None
    log_json: Annotated[
        bool | None,
        Parameter(name=["--log-json"], help="Output logs as JSON"),
    ] = None
    log_file: Annotated[
        str | None,
        Parameter(name=["--log-file"], help="Log file path"),
    ] = None


def _configure_logging(config: LogConfig) -> None:
    """Configure logging from CLI flags with env var fallback."""
    level = config.log_level or os.getenv("LOG_LEVEL", "INFO")
    json_output = config.log_json if config.log_json is not None else (
        os.getenv("LOG_JSON", "").lower() in ("true", "1", "yes")
    )
    log_file = config.log_file or os.getenv("LOG_FILE")
    setup_logging(level=level, json_output=json_output, log_file=log_file)
```

Each command function adds `log: LogConfig = LogConfig()` as a parameter and calls `_configure_logging(log)` at the start.

**Commit:** `feat(cli): add --log-level, --log-json, --log-file flags to all commands`

## Done When

- [ ] All 5 CLI commands accept `--log-level`, `--log-json`, `--log-file`
- [ ] Environment variables provide defaults when flags are not passed
- [ ] CLI flags override environment variables
- [ ] `setup_logging()` is called before scraper initialization in each command
- [ ] `make check` passes
