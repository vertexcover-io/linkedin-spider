"""End-to-end tests for linkedin-spider scraper actions.

One scrape call per test.  Non-deterministic outputs are validated by
structure, types, and minimum result counts — not exact values.
Parametrized where multiple inputs exercise different code paths.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from linkedin_spider.core.scraper import LinkedinSpider

PROFILE_URLS = [
    "https://www.linkedin.com/in/williamhgates/",
    "https://www.linkedin.com/in/satyanadella/",
]
COMPANY_URLS = [
    "https://www.linkedin.com/company/microsoft/",
    "https://www.linkedin.com/company/google/",
]
PROFILE_EXPECTED_KEYS = {
    "name",
    "headline",
    "location",
    "about",
    "experience",
    "education",
    "profile_url",
}
COMPANY_EXPECTED_KEYS = {
    "name",
    "company_url",
    "tagline",
    "industry",
    "location",
    "followers",
    "employee_count",
}


def _assert_non_empty_str(value: Any, field: str) -> None:
    assert isinstance(value, str), f"{field} should be str, got {type(value)}"
    assert value and value != "N/A", f"{field} should not be empty/N/A"


# ── profile ────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.parametrize("profile_url", PROFILE_URLS)
def test_scrape_profile(spider: LinkedinSpider, profile_url: str) -> None:
    result = spider.scrape_profile(profile_url)

    assert result is not None, "scrape_profile returned None"
    assert PROFILE_EXPECTED_KEYS.issubset(result.keys()), (
        f"Missing keys: {PROFILE_EXPECTED_KEYS - result.keys()}"
    )
    _assert_non_empty_str(result["name"], "name")
    assert isinstance(result["experience"], list)
    assert isinstance(result["education"], list)
    assert result["profile_url"] == profile_url


@pytest.mark.integration
def test_scrape_profile_invalid_url(spider: LinkedinSpider) -> None:
    assert spider.scrape_profile("https://example.com/not-a-profile") is None


# ── company ────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.parametrize("company_url", COMPANY_URLS)
def test_scrape_company(spider: LinkedinSpider, company_url: str) -> None:
    result = spider.scrape_company(company_url)

    assert result is not None, "scrape_company returned None"
    assert COMPANY_EXPECTED_KEYS.issubset(result.keys()), (
        f"Missing keys: {COMPANY_EXPECTED_KEYS - result.keys()}"
    )
    _assert_non_empty_str(result["name"], "name")
    assert result["company_url"] == company_url


@pytest.mark.integration
def test_scrape_company_invalid_url(spider: LinkedinSpider) -> None:
    assert spider.scrape_company("https://example.com/not-a-company") is None


# ── search profiles ───────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "max_results", "filters"),
    [
        ("software engineer", 3, None),
        ("AI Growth", 2, {"location": "Surat"}),
        ("software engineer", 2, {"current_company": "Google"}),
        ("data scientist", 2, {"connections": "1"}),
    ],
    ids=["no-filter", "location-filter", "current-company-filter", "connections-1st"],
)
def test_search_profiles(
    spider: LinkedinSpider,
    query: str,
    max_results: int,
    filters: dict[str, str] | None,
) -> None:
    results = spider.search_profiles(query, max_results=max_results, filters=filters)

    assert isinstance(results, list)
    assert len(results) >= 1, f"Expected at least 1 result for '{query}'"
    assert len(results) <= max_results

    first = results[0]
    expected_keys = {"name", "headline", "location", "profile_url"}
    assert expected_keys.issubset(first.keys()), f"Missing keys: {expected_keys - first.keys()}"


# ── search filter application ─────────────────────────────────────────────


def _applied_filters(spider: LinkedinSpider) -> dict[str, Any]:
    scraper = spider.search_scraper
    assert scraper is not None, "search_scraper not initialized"
    return cast("dict[str, Any]", scraper.filter_handler.get_applied_filters())  # type: ignore[unreachable]


def _current_url(spider: LinkedinSpider) -> str:
    driver = spider.driver_manager.driver
    assert driver is not None, "driver not initialized"
    return str(driver.current_url)


@pytest.mark.integration
def test_search_location_filter_applies(spider: LinkedinSpider) -> None:
    """Location filter must produce a geoUrn in the final URL and surface in applied_filters."""
    spider.search_profiles("AI Growth", max_results=2, filters={"location": "Surat"})

    applied = _applied_filters(spider)
    assert "location" in applied, f"Location filter not recorded; got {applied}"
    assert applied["location"].get("urn"), "Location filter did not resolve to a urn"

    current_url = _current_url(spider)
    assert "geoUrn=" in current_url, f"geoUrn missing from final URL: {current_url}"


@pytest.mark.integration
def test_search_connections_filter_applies(spider: LinkedinSpider) -> None:
    """Connections=1st must add network=[\"F\"] to the URL."""
    spider.search_profiles("data scientist", max_results=2, filters={"connections": "1"})

    applied = _applied_filters(spider)
    assert applied.get("connections", {}).get("network") == ["F"]

    current_url = _current_url(spider)
    assert "network=" in current_url, f"network param missing from URL: {current_url}"


@pytest.mark.integration
def test_search_current_company_filter_applies(spider: LinkedinSpider) -> None:
    """Current company filter must produce a currentCompany URN."""
    spider.search_profiles(
        "software engineer", max_results=2, filters={"current_company": "Google"}
    )

    applied = _applied_filters(spider)
    assert "current_company" in applied, f"Current company filter not recorded; got {applied}"
    assert applied["current_company"].get("urn"), "currentCompany did not resolve"

    current_url = _current_url(spider)
    assert "currentCompany=" in current_url, f"currentCompany missing from URL: {current_url}"


@pytest.mark.integration
def test_search_location_geo_urn_cache_persists(spider: LinkedinSpider) -> None:
    """Second call with same location should hit cache (cached=True in applied filters)."""
    spider.search_profiles("AI Growth", max_results=2, filters={"location": "Surat"})
    spider.search_profiles("AI", max_results=2, filters={"location": "Surat"})

    applied = _applied_filters(spider)
    assert applied["location"].get("cached") is True, "Second call should have hit the geoUrn cache"


@pytest.mark.integration
def test_search_connections_multi_network(spider: LinkedinSpider) -> None:
    """Connections=1,2 must add network=[\"F\",\"S\"] to the URL."""
    spider.search_profiles("data scientist", max_results=2, filters={"connections": "1,2"})

    applied = _applied_filters(spider)
    assert applied.get("connections", {}).get("network") == ["F", "S"]

    current_url = _current_url(spider)
    assert "network=" in current_url, f"network param missing from URL: {current_url}"
    assert "%22F%22" in current_url and "%22S%22" in current_url, (
        f"both network codes should appear in URL: {current_url}"
    )


@pytest.mark.integration
def test_search_connection_of_filter_applies(spider: LinkedinSpider) -> None:
    """connection_of resolves a profile URL to its URN and applies connectionOf=."""
    spider.search_profiles(
        "AI Growth",
        max_results=2,
        filters={"connection_of": "https://www.linkedin.com/in/williamhgates/"},
    )

    applied = _applied_filters(spider)
    assert "connection_of" in applied, f"connection_of not recorded; got {applied}"
    assert applied["connection_of"].get("urn"), "connection_of did not resolve a URN"

    current_url = _current_url(spider)
    assert "connectionOf=" in current_url, f"connectionOf missing from URL: {current_url}"


# ── search posts ──────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.parametrize(
    ("keywords", "date_posted"),
    [
        ("artificial intelligence", None),
        ("startup funding", "past-week"),
    ],
    ids=["no-date-filter", "past-week"],
)
def test_search_posts(
    spider: LinkedinSpider,
    keywords: str,
    date_posted: str | None,
) -> None:
    results = spider.search_posts(
        keywords,
        max_results=2,
        max_comments=0,
        date_posted=date_posted,
    )

    assert isinstance(results, list)
    assert len(results) >= 1, f"Expected at least 1 post for '{keywords}'"

    post = results[0]
    expected_keys = {
        "author_name",
        "author_headline",
        "author_profile_url",
        "post_text",
        "hashtags",
        "links",
        "post_url",
        "likes_count",
        "comments_count",
        "reposts_count",
    }
    assert expected_keys.issubset(post.keys()), f"Missing keys: {expected_keys - post.keys()}"
    assert isinstance(post["likes_count"], int)
    assert isinstance(post["comments_count"], int)
    assert isinstance(post["reposts_count"], int)
    assert isinstance(post["hashtags"], list)
    assert isinstance(post["links"], list)


# ── conversations list ────────────────────────────────────────────────────


@pytest.mark.integration
def test_scrape_conversations_list(spider: LinkedinSpider) -> None:
    results = spider.scrape_conversations_list(max_results=3)

    assert isinstance(results, list)
    if not results:
        pytest.skip("No conversations available")

    convo = results[0]
    expected_keys = {"participant_name", "timestamp", "message_snippet"}
    assert expected_keys.issubset(convo.keys()), f"Missing keys: {expected_keys - convo.keys()}"


# ── conversation messages ─────────────────────────────────────────────────


@pytest.mark.integration
def test_scrape_conversation_messages(spider: LinkedinSpider) -> None:
    result = spider.scrape_conversation_messages()

    assert result is not None
    assert "messages" in result
    assert "total_messages" in result
    assert isinstance(result["messages"], list)
    assert isinstance(result["total_messages"], int)


# ── incoming connections ──────────────────────────────────────────────────


@pytest.mark.integration
def test_scrape_incoming_connections(spider: LinkedinSpider) -> None:
    results = spider.scrape_incoming_connections(max_results=3)

    assert isinstance(results, list)
    if not results:
        pytest.skip("No incoming connections available")

    conn = results[0]
    expected_keys = {"name", "profile_url", "headline"}
    assert expected_keys.issubset(conn.keys()), f"Missing keys: {expected_keys - conn.keys()}"


# ── outgoing connections ──────────────────────────────────────────────────


@pytest.mark.integration
def test_scrape_outgoing_connections(spider: LinkedinSpider) -> None:
    results = spider.scrape_outgoing_connections(max_results=3)

    assert isinstance(results, list)
    if not results:
        pytest.skip("No outgoing connections available")

    conn = results[0]
    expected_keys = {"name", "profile_url", "headline"}
    assert expected_keys.issubset(conn.keys()), f"Missing keys: {expected_keys - conn.keys()}"


# ── send message (dry run) ────────────────────────────────────────────────


@pytest.mark.integration
def test_send_message_dry_run_existing_conversation(spider: LinkedinSpider) -> None:
    conversations = spider.scrape_conversations_list(max_results=1)
    if not conversations:
        pytest.skip("No conversations available for dry-run test")

    participant_name = conversations[0]["participant_name"]
    result = spider.send_message(
        message="dry run test message",
        participant_name=participant_name,
        dry_run=True,
    )
    assert result is True, f"Dry run failed for existing conversation with {participant_name}"


@pytest.mark.integration
@pytest.mark.parametrize("profile_url", PROFILE_URLS[:1], ids=["new-conversation"])
def test_send_message_dry_run_new_conversation(spider: LinkedinSpider, profile_url: str) -> None:
    result = spider.send_message(
        message="dry run test message",
        profile_url=profile_url,
        dry_run=True,
    )
    assert result is True, f"Dry run failed for new conversation with {profile_url}"


@pytest.mark.integration
def test_send_message_dry_run_empty_message(spider: LinkedinSpider) -> None:
    result = spider.send_message(
        message="",
        participant_name="test",
        dry_run=True,
    )
    assert result is False


@pytest.mark.integration
def test_send_message_dry_run_both_targets(spider: LinkedinSpider) -> None:
    result = spider.send_message(
        message="test",
        participant_name="test",
        profile_url="https://www.linkedin.com/in/test/",
        dry_run=True,
    )
    assert result is False


# ── keep alive ────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_keep_alive(spider: LinkedinSpider) -> None:
    assert spider.keep_alive() is True
