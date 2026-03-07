from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator

import pytest
from dotenv import load_dotenv
from fastmcp import Client

import linkedin_spider.mcp.server as mcp_server
from linkedin_spider.core.config import ScraperConfig
from linkedin_spider.core.scraper import LinkedinSpider
from linkedin_spider.mcp.server import mcp_app

load_dotenv()


@pytest.fixture(scope="session")
def spider() -> Generator[LinkedinSpider, None, None]:
    """Session-scoped LinkedinSpider authenticated via LINKEDIN_COOKIE from .env."""
    cookie = os.environ.get("LINKEDIN_COOKIE")
    if not cookie:
        pytest.skip("LINKEDIN_COOKIE not set in environment")

    config = ScraperConfig(headless=True)
    scraper = LinkedinSpider(li_at_cookie=cookie, config=config)
    yield scraper
    scraper.close()


@pytest.fixture(scope="session")
def mcp_scraper(spider: LinkedinSpider) -> Generator[LinkedinSpider, None, None]:
    """Inject the session-scoped spider into the MCP server global, reset on teardown."""
    mcp_server._scraper_instance = spider
    yield spider
    mcp_server._scraper_instance = None


@pytest.fixture
async def mcp_client() -> AsyncGenerator[Client, None]:
    """Provide a connected FastMCP Client for in-memory MCP testing."""
    async with Client(mcp_app) as client:
        yield client
