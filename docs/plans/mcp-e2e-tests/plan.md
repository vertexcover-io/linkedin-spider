# Plan: MCP Server E2E Tests

> **Source:** Feature request
> **Created:** 2026-03-07
> **Status:** planning

## Goal

Add comprehensive MCP-level tests that verify tool registration, parameter validation, error handling, and full-stack e2e behavior through the FastMCP protocol.

## Acceptance Criteria

- [ ] All 11 MCP tools verified as registered with correct names and parameter schemas
- [ ] Parameter validation tested (empty required fields raise ToolError)
- [ ] Uninitialized scraper behavior tested (error strings returned, not crashes)
- [ ] Full e2e tests through MCP protocol for all scraper tools (integration, needs LINKEDIN_COOKIE)
- [ ] `make check` and `make test` pass
- [ ] Phase 1 tests run without credentials; Phase 2 tests skip without LINKEDIN_COOKIE

## Codebase Context

### Existing Patterns to Follow

- **Test structure**: `tests/test_e2e.py` — class-based tests with structural assertions, `pytest.skip` for missing data
- **Fixtures**: `tests/conftest.py` — session-scoped `spider` fixture with LINKEDIN_COOKIE guard
- **MCP server**: `src/linkedin_spider/mcp/server.py` — `mcp_app = FastMCP("linkedin-spider")`, global `_scraper_instance`, `get_scraper()` accessor

### Test Infrastructure

- pytest + pytest-asyncio, run via `uv run python -m pytest`
- Markers: `slow`, `integration`
- `fastmcp.Client` available for in-memory MCP testing (no subprocess needed)

### Key Details

- Tools return JSON strings (some with `"label:\n"` prefix, `scrape_profile` returns raw JSON)
- Tools with validation raise `ValueError` on empty required params → FastMCP converts to `ToolError`
- Tools catch `Exception` internally and return error message strings
- `reset_session` modifies global `_scraper_instance` — needs state restoration in tests

## Phases

| #   | Phase                                                              | Status  | Depends On |
| --- | ------------------------------------------------------------------ | ------- | ---------- |
| 1   | MCP protocol tests (registration, validation, uninitialized state) | pending | —          |
| 2   | MCP e2e integration tests (full stack through MCP protocol)        | pending | Phase 1    |

## Phase Dependency Graph

Phase 1 --> Phase 2
