# Phase 1: MCP Protocol Tests

> **Status:** pending
> **Depends on:** none

## Overview

Tests that verify the MCP server's tool registration, parameter schemas, input validation, and error handling when the scraper is not initialized. These run without LinkedIn credentials.

## Implementation

**Files:**

- Create: `tests/test_mcp_server.py`
- Modify: `tests/conftest.py` — add `mcp_client` async fixture
- Modify: `pyproject.toml` — add `asyncio_mode = "auto"`

**What to test:**

### 1. Tool Registration (`TestToolRegistration`)

- Exactly 11 tools registered, names match expected set
- Each tool's required params and defaults verified:
  - `scrape_profile`: requires `profile_url`
  - `search_profiles`: requires `query`, `max_results` defaults to 5, 8 total params
  - `get_session_status`: no params
  - `reset_session`: no params
  - `scrape_company`: requires `company_url`
  - `search_posts`: requires `keywords`, `scroll_pause` defaults to 2.0, `max_comments` defaults to 10
  - `scrape_incoming_connections`: `max_results` defaults to 10
  - `scrape_outgoing_connections`: `max_results` defaults to 10
  - `scrape_conversations_list`: `max_results` defaults to 10
  - `scrape_conversation`: `participant_name` optional/nullable
  - `send_connection_request`: requires `profile_url`, `note` optional

### 2. Parameter Validation (`TestParameterValidation`)

- Empty `profile_url` on `scrape_profile` → `ToolError`
- Empty `query` on `search_profiles` → `ToolError`
- Empty `company_url` on `scrape_company` → `ToolError`
- Empty `keywords` on `search_posts` → `ToolError`
- Empty `profile_url` on `send_connection_request` → `ToolError`

### 3. Uninitialized Scraper (`TestUninitializedScraper`)

- Direct `get_scraper()` call raises `RuntimeError`
- Each of 10 tools (except `reset_session`) returns error string containing "Scraper not initialized"
- `reset_session` succeeds even when uninitialized (returns "reset successfully")

**What to build:**

Key fixture — `mcp_client` in conftest.py:

```python
@pytest.fixture
async def mcp_client() -> AsyncGenerator[Client, None]:
    async with Client(mcp_app) as client:
        yield client
```

Key fixture — ensuring no scraper (defined inside `TestUninitializedScraper`):

```python
@pytest.fixture(autouse=True)
def _ensure_no_scraper() -> Generator[None, None, None]:
    original = mcp_server._scraper_instance
    mcp_server._scraper_instance = None
    yield
    mcp_server._scraper_instance = original
```

Helper for extracting text from `CallToolResult`:

```python
def _result_text(result: Any) -> str:
    assert result.content
    return result.content[0].text
```

Helper for tool schema inspection:

```python
def _find_tool(tools: list[Any], name: str) -> Any:
    for t in tools:
        if t.name == name:
            return t
    raise AssertionError(f"Tool '{name}' not found")
```

**Commit:** `test(mcp): add protocol, validation, and uninitialized state tests`

## Done When

- [ ] 11+ tool registration tests pass
- [ ] 5 parameter validation tests pass
- [ ] 12 uninitialized scraper tests pass
- [ ] All run without LINKEDIN_COOKIE: `uv run python -m pytest tests/test_mcp_server.py -m "not integration"`
- [ ] `make check` passes
