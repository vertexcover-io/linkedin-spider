"""MCP server tests: tool registration, parameter validation, and e2e through MCP protocol.

Phase 1 tests (no credentials): TestToolRegistration, TestParameterValidation, TestUninitializedScraper
Phase 2 tests (integration): TestMcpScrapeProfile, TestMcpScrapeCompany, TestMcpSearchProfiles,
    TestMcpSearchPosts, TestMcpConversations, TestMcpConnections, TestMcpSessionStatus
"""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import linkedin_spider.mcp.server as mcp_server
from linkedin_spider.core.scraper import LinkedinSpider
from linkedin_spider.mcp.server import get_scraper

PROFILE_URL = "https://www.linkedin.com/in/williamhgates/"
COMPANY_URL = "https://www.linkedin.com/company/microsoft/"

EXPECTED_TOOL_NAMES = {
    "scrape_profile",
    "search_profiles",
    "get_session_status",
    "reset_session",
    "scrape_incoming_connections",
    "scrape_outgoing_connections",
    "scrape_company",
    "search_posts",
    "scrape_conversations_list",
    "scrape_conversation",
    "send_connection_request",
}


# ── helpers ────────────────────────────────────────────────────────────────


def _result_text(result: Any) -> str:
    """Extract text content from a CallToolResult."""
    assert result.content, "CallToolResult has no content"
    return result.content[0].text  # type: ignore[no-any-return]


def _parse_prefixed_json(text: str) -> Any:
    """Parse JSON from MCP tool responses that have a 'label:\\n' prefix."""
    if "\n" in text:
        _, json_str = text.split("\n", 1)
        return json.loads(json_str)
    return json.loads(text)


def _find_tool(tools: list[Any], name: str) -> Any:
    for t in tools:
        if t.name == name:
            return t
    raise AssertionError(f"Tool '{name}' not found in registered tools")


def _tool_required_params(tool: Any) -> list[str]:
    return tool.inputSchema.get("required", [])  # type: ignore[no-any-return]


def _tool_param_names(tool: Any) -> set[str]:
    return set(tool.inputSchema.get("properties", {}).keys())


def _tool_param_default(tool: Any, param: str) -> Any:
    return tool.inputSchema["properties"][param].get("default")


# ── Phase 1: Tool Registration ────────────────────────────────────────────


class TestToolRegistration:
    async def test_exactly_11_tools_registered(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool_names = {t.name for t in tools}
        assert tool_names == EXPECTED_TOOL_NAMES

    async def test_scrape_profile_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "scrape_profile")
        assert _tool_required_params(tool) == ["profile_url"]
        assert _tool_param_names(tool) == {"profile_url"}

    async def test_search_profiles_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "search_profiles")
        assert "query" in _tool_required_params(tool)
        assert len(_tool_param_names(tool)) == 8
        assert _tool_param_default(tool, "max_results") == 5

    async def test_get_session_status_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "get_session_status")
        assert _tool_required_params(tool) == []
        assert _tool_param_names(tool) == set()

    async def test_reset_session_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "reset_session")
        assert _tool_required_params(tool) == []
        assert _tool_param_names(tool) == set()

    async def test_scrape_company_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "scrape_company")
        assert _tool_required_params(tool) == ["company_url"]

    async def test_search_posts_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "search_posts")
        assert "keywords" in _tool_required_params(tool)
        assert _tool_param_default(tool, "scroll_pause") == 2.0
        assert _tool_param_default(tool, "max_comments") == 10

    async def test_scrape_incoming_connections_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "scrape_incoming_connections")
        assert _tool_required_params(tool) == []
        assert _tool_param_default(tool, "max_results") == 10

    async def test_scrape_outgoing_connections_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "scrape_outgoing_connections")
        assert _tool_required_params(tool) == []
        assert _tool_param_default(tool, "max_results") == 10

    async def test_scrape_conversations_list_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "scrape_conversations_list")
        assert _tool_required_params(tool) == []
        assert _tool_param_default(tool, "max_results") == 10

    async def test_scrape_conversation_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "scrape_conversation")
        assert _tool_required_params(tool) == []
        assert "participant_name" in _tool_param_names(tool)

    async def test_send_connection_request_params(self, mcp_client: Client) -> None:
        tools = await mcp_client.list_tools()
        tool = _find_tool(tools, "send_connection_request")
        assert "profile_url" in _tool_required_params(tool)
        assert "note" in _tool_param_names(tool)


# ── Phase 1: Parameter Validation ─────────────────────────────────────────


class TestParameterValidation:
    async def test_scrape_profile_empty_url(self, mcp_client: Client) -> None:
        with pytest.raises(ToolError, match="profile_url is required"):
            await mcp_client.call_tool("scrape_profile", {"profile_url": ""})

    async def test_search_profiles_empty_query(self, mcp_client: Client) -> None:
        with pytest.raises(ToolError, match="query is required"):
            await mcp_client.call_tool("search_profiles", {"query": ""})

    async def test_scrape_company_empty_url(self, mcp_client: Client) -> None:
        with pytest.raises(ToolError, match="company_url is required"):
            await mcp_client.call_tool("scrape_company", {"company_url": ""})

    async def test_search_posts_empty_keywords(self, mcp_client: Client) -> None:
        with pytest.raises(ToolError, match="keywords is required"):
            await mcp_client.call_tool("search_posts", {"keywords": ""})

    async def test_send_connection_request_empty_url(self, mcp_client: Client) -> None:
        with pytest.raises(ToolError, match="profile_url is required"):
            await mcp_client.call_tool("send_connection_request", {"profile_url": ""})


# ── Phase 1: Uninitialized Scraper ────────────────────────────────────────


class TestUninitializedScraper:
    @pytest.fixture(autouse=True)
    def _ensure_no_scraper(self) -> Generator[None, None, None]:
        original = mcp_server._scraper_instance
        mcp_server._scraper_instance = None
        yield
        mcp_server._scraper_instance = original

    def test_get_scraper_raises_runtime_error(self) -> None:
        with pytest.raises(RuntimeError, match="Scraper not initialized"):
            get_scraper()

    async def test_scrape_profile_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_profile", {"profile_url": PROFILE_URL})
        assert "Scraper not initialized" in _result_text(result)

    async def test_search_profiles_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("search_profiles", {"query": "test"})
        assert "Scraper not initialized" in _result_text(result)

    async def test_get_session_status_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("get_session_status", {})
        assert "Scraper not initialized" in _result_text(result)

    async def test_scrape_company_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_company", {"company_url": COMPANY_URL})
        assert "Scraper not initialized" in _result_text(result)

    async def test_search_posts_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("search_posts", {"keywords": "test"})
        assert "Scraper not initialized" in _result_text(result)

    async def test_scrape_incoming_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_incoming_connections", {})
        assert "Scraper not initialized" in _result_text(result)

    async def test_scrape_outgoing_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_outgoing_connections", {})
        assert "Scraper not initialized" in _result_text(result)

    async def test_conversations_list_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_conversations_list", {})
        assert "Scraper not initialized" in _result_text(result)

    async def test_scrape_conversation_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_conversation", {})
        assert "Scraper not initialized" in _result_text(result)

    async def test_send_connection_request_returns_error(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("send_connection_request", {"profile_url": PROFILE_URL})
        assert "Scraper not initialized" in _result_text(result)

    async def test_reset_session_succeeds_when_uninitialized(self, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("reset_session", {})
        assert "reset successfully" in _result_text(result)


# ── Phase 2: Integration helpers ──────────────────────────────────────────


def _assert_non_empty_str(value: Any, field: str) -> None:
    assert isinstance(value, str), f"{field} should be str, got {type(value)}"
    assert value and value != "N/A", f"{field} should not be empty/N/A"


@pytest.fixture
def _restore_scraper_after() -> Generator[None, None, None]:
    original = mcp_server._scraper_instance
    yield
    mcp_server._scraper_instance = original


# ── Phase 2: Scrape Profile ──────────────────────────────────────────────


@pytest.mark.integration
class TestMcpScrapeProfile:
    async def test_returns_json_with_profile_keys(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_profile", {"profile_url": PROFILE_URL})
        data = json.loads(_result_text(result))
        expected_keys = {
            "name",
            "headline",
            "location",
            "about",
            "experience",
            "education",
            "profile_url",
        }
        assert expected_keys.issubset(data.keys()), f"Missing keys: {expected_keys - data.keys()}"

    async def test_name_is_populated(self, mcp_scraper: LinkedinSpider, mcp_client: Client) -> None:
        result = await mcp_client.call_tool("scrape_profile", {"profile_url": PROFILE_URL})
        data = json.loads(_result_text(result))
        _assert_non_empty_str(data["name"], "name")

    async def test_experience_is_list(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_profile", {"profile_url": PROFILE_URL})
        data = json.loads(_result_text(result))
        assert isinstance(data["experience"], list), "experience should be a list"

    async def test_invalid_url_returns_failure_message(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "scrape_profile", {"profile_url": "https://example.com/not-a-profile"}
        )
        assert "Failed to scrape profile" in _result_text(result)


# ── Phase 2: Scrape Company ──────────────────────────────────────────────


@pytest.mark.integration
class TestMcpScrapeCompany:
    async def test_returns_json_with_company_keys(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_company", {"company_url": COMPANY_URL})
        data = _parse_prefixed_json(_result_text(result))
        expected_keys = {"name", "company_url"}
        assert expected_keys.issubset(data.keys()), f"Missing keys: {expected_keys - data.keys()}"

    async def test_company_name_is_populated(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_company", {"company_url": COMPANY_URL})
        data = _parse_prefixed_json(_result_text(result))
        _assert_non_empty_str(data["name"], "name")

    async def test_invalid_url_returns_failure_message(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "scrape_company", {"company_url": "https://example.com/not-a-company"}
        )
        assert "Failed to scrape company" in _result_text(result)


# ── Phase 2: Search Profiles ─────────────────────────────────────────────


@pytest.mark.integration
class TestMcpSearchProfiles:
    async def test_returns_list_of_results(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "search_profiles", {"query": "software engineer", "max_results": 3}
        )
        data = _parse_prefixed_json(_result_text(result))
        assert isinstance(data, list), "search_profiles should return a list"
        assert len(data) >= 1, "Should return at least 1 result"
        assert len(data) <= 3, "Should respect max_results"

    async def test_result_has_expected_keys(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "search_profiles", {"query": "data scientist", "max_results": 2}
        )
        data = _parse_prefixed_json(_result_text(result))
        assert len(data) >= 1
        expected_keys = {"name", "headline", "location", "profile_url"}
        assert expected_keys.issubset(data[0].keys())


# ── Phase 2: Search Posts ─────────────────────────────────────────────────


@pytest.mark.integration
class TestMcpSearchPosts:
    async def test_returns_list_of_posts(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "search_posts",
            {"keywords": "artificial intelligence", "max_results": 2, "max_comments": 0},
        )
        data = _parse_prefixed_json(_result_text(result))
        assert isinstance(data, list), "search_posts should return a list"
        assert len(data) >= 1, "Should return at least 1 post"

    async def test_post_has_expected_keys(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "search_posts", {"keywords": "machine learning", "max_results": 1, "max_comments": 0}
        )
        data = _parse_prefixed_json(_result_text(result))
        assert len(data) >= 1
        expected_keys = {
            "author_name",
            "post_text",
            "likes_count",
            "comments_count",
            "reposts_count",
        }
        assert expected_keys.issubset(data[0].keys())

    async def test_engagement_metrics_are_ints(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool(
            "search_posts", {"keywords": "python programming", "max_results": 1, "max_comments": 0}
        )
        data = _parse_prefixed_json(_result_text(result))
        assert len(data) >= 1
        post = data[0]
        assert isinstance(post["likes_count"], int)
        assert isinstance(post["comments_count"], int)
        assert isinstance(post["reposts_count"], int)


# ── Phase 2: Conversations ───────────────────────────────────────────────


@pytest.mark.integration
class TestMcpConversations:
    async def test_conversations_list_returns_result(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_conversations_list", {"max_results": 3})
        text = _result_text(result)
        # Either JSON list or "No conversations found"
        assert "conversations" in text.lower() or "no conversations" in text.lower()

    async def test_conversation_has_expected_keys(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_conversations_list", {"max_results": 3})
        text = _result_text(result)
        if "No conversations found" in text:
            pytest.skip("No conversations available to test")
        data = _parse_prefixed_json(text)
        assert len(data) >= 1
        expected_keys = {"participant_name", "timestamp", "message_snippet"}
        assert expected_keys.issubset(data[0].keys())

    async def test_scrape_conversation_returns_messages(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_conversation", {})
        text = _result_text(result)
        if "No messages found" in text:
            pytest.skip("No conversation messages available")
        data = _parse_prefixed_json(text)
        assert "messages" in data
        assert isinstance(data["messages"], list)


# ── Phase 2: Connections ─────────────────────────────────────────────────


@pytest.mark.integration
class TestMcpConnections:
    async def test_incoming_connections_returns_result(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_incoming_connections", {"max_results": 3})
        text = _result_text(result)
        assert "incoming" in text.lower() or "no incoming" in text.lower()

    async def test_outgoing_connections_returns_result(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_outgoing_connections", {"max_results": 3})
        text = _result_text(result)
        assert "outgoing" in text.lower() or "no outgoing" in text.lower()

    async def test_connection_has_expected_keys(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("scrape_incoming_connections", {"max_results": 3})
        text = _result_text(result)
        if "No incoming" in text:
            pytest.skip("No incoming connections available")
        data = _parse_prefixed_json(text)
        assert len(data) >= 1
        expected_keys = {"name", "profile_url", "headline"}
        assert expected_keys.issubset(data[0].keys())


# ── Phase 2: Session Status ──────────────────────────────────────────────


@pytest.mark.integration
class TestMcpSessionStatus:
    async def test_session_status_active(
        self, mcp_scraper: LinkedinSpider, mcp_client: Client
    ) -> None:
        result = await mcp_client.call_tool("get_session_status", {})
        assert "Active" in _result_text(result)

    async def test_reset_session_returns_success(
        self,
        mcp_scraper: LinkedinSpider,
        mcp_client: Client,
        _restore_scraper_after: None,
    ) -> None:
        result = await mcp_client.call_tool("reset_session", {})
        assert "reset successfully" in _result_text(result)
