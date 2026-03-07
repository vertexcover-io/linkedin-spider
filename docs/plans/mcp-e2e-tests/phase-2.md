# Phase 2: MCP E2E Integration Tests

> **Status:** pending
> **Depends on:** Phase 1

## Overview

Full-stack tests that call MCP tools through `fastmcp.Client`, with a real `LinkedinSpider` injected into the MCP server's global state. These mirror `test_e2e.py` assertions but exercise the MCP protocol layer.

## Implementation

**Files:**

- Modify: `tests/test_mcp_server.py` — add integration test classes
- Modify: `tests/conftest.py` — add `mcp_scraper` session-scoped fixture

**Pattern to follow:** `tests/test_e2e.py` — structural assertions, `pytest.skip` for empty data

**What to test (all `@pytest.mark.integration`):**

| Class                   | Tests                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| `TestMcpScrapeProfile`  | JSON has expected keys, name populated, experience is list, invalid URL returns failure message |
| `TestMcpScrapeCompany`  | JSON has expected keys (name, company_url), name populated, invalid URL returns failure         |
| `TestMcpSearchProfiles` | Returns list with 1+ results respecting max_results, result has expected keys                   |
| `TestMcpSearchPosts`    | Returns list of posts, post has expected keys, engagement metrics are ints                      |
| `TestMcpConversations`  | Conversations list returns JSON or "No conversations", conversation has expected keys           |
| `TestMcpConnections`    | Incoming/outgoing return JSON or "No ... found", connections have expected keys                 |
| `TestMcpSessionStatus`  | Status contains "Active", reset returns success (with state restoration)                        |

**What to build:**

Key fixture — `mcp_scraper` in conftest.py:

```python
@pytest.fixture(scope="session")
def mcp_scraper(spider: LinkedinSpider) -> Generator[LinkedinSpider, None, None]:
    mcp_server._scraper_instance = spider
    yield spider
    mcp_server._scraper_instance = None
```

Session-scoped, depends on existing `spider` fixture. Phase 2 tests declare `mcp_scraper` as a parameter for its side effect (setting `_scraper_instance`).

Key fixture — state restoration for `reset_session` test:

```python
@pytest.fixture
def _restore_scraper_after() -> Generator[None, None, None]:
    original = mcp_server._scraper_instance
    yield
    mcp_server._scraper_instance = original
```

Helper — JSON parsing for prefixed responses:

Several tools return `f"label:\n{json.dumps(data)}"`. Helper needed:

```python
def _parse_prefixed_json(text: str) -> Any:
    if "\n" in text:
        _, json_str = text.split("\n", 1)
        return json.loads(json_str)
    return json.loads(text)
```

Note: `scrape_profile` returns raw JSON (no prefix), while `scrape_company` returns `"company_profile:\n{json}"`, `search_profiles` returns `"profiles:\n{json}"`, etc.

**Commit:** `test(mcp): add e2e integration tests through MCP protocol`

## Done When

- [ ] All integration tests pass with LINKEDIN_COOKIE set
- [ ] Tests skip gracefully without LINKEDIN_COOKIE
- [ ] `make check` passes
- [ ] `make test` passes
