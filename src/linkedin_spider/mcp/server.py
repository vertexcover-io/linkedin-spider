import json
import logging
import os
import sys
from typing import Annotated

from cyclopts import App, Parameter
from dotenv import load_dotenv
from fastmcp import FastMCP

from linkedin_spider import LinkedinSpider, ScraperConfig

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

cli_app = App(name="linkedin-spider-mcp", help="LinkedIn Spider MCP Server")
mcp_app = FastMCP("linkedin-spider")

_scraper_instance = None


def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        logger.info("Scraper not initialized yet, initializing now...")
        try:
            _initialize_scraper(
                email=os.getenv("LINKEDIN_EMAIL"),
                password=os.getenv("LINKEDIN_PASSWORD"),
                cookie=os.getenv("LINKEDIN_COOKIE"),
                headless=os.getenv("HEADLESS", "true").lower() == "true",
                proxy=os.getenv("PROXY_SERVER"),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize scraper: {e}") from e
    return _scraper_instance


@mcp_app.tool()
async def scrape_profile(profile_url: str) -> str:
    if not profile_url:
        raise ValueError("profile_url is required")

    try:
        scraper = get_scraper()
        result = scraper.scrape_profile(profile_url)

        if result:
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return f"Failed to scrape profile: {profile_url}"

    except Exception as e:
        return f"Error scraping profile {profile_url}: {e!s}"


@mcp_app.tool()
async def search_profiles(
    query: str,
    max_results: int = 5,
    location: str | None = None,
    industry: str | None = None,
    current_company: str | None = None,
    connections: str | None = None,
    connection_of: str | None = None,
    followers_of: str | None = None,
) -> str:
    if not query:
        raise ValueError("query is required")

    try:
        scraper = get_scraper()

        filters = {}
        if location:
            filters["location"] = location
        if industry:
            filters["industry"] = industry
        if current_company:
            filters["current_company"] = current_company
        if connections:
            filters["connections"] = connections
        if connection_of:
            filters["connection_of"] = connection_of
        if followers_of:
            filters["followers_of"] = followers_of

        results = scraper.scrape_search_results(query, max_results, filters if filters else None)

        if results:
            return f"profiles:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        else:
            return f"No profiles found for query: {query}"

    except Exception as e:
        return f"Error searching profiles for '{query}': {e!s}"


@mcp_app.tool()
async def get_session_status() -> str:
    try:
        scraper = get_scraper()
        is_active = scraper.keep_alive()
        status = "Active" if is_active else "Inactive"
        return f"LinkedIn browser session status: {status}"

    except Exception as e:
        return f"Error checking session status: {e!s}"


@mcp_app.tool()
async def reset_session() -> str:
    global _scraper_instance
    try:
        if _scraper_instance:
            _scraper_instance.close()
            _scraper_instance = None
        return "LinkedIn browser session has been reset successfully"

    except Exception as e:
        return f"Error resetting session: {e!s}"


@mcp_app.tool()
async def scrape_incoming_connections(max_results: int = 10) -> str:
    try:
        scraper = get_scraper()
        results = scraper.scrape_incoming_connections(max_results)

        if results:
            return f"incoming_connections:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        else:
            return "No incoming connection requests found"

    except Exception as e:
        return f"Error scraping incoming connections: {e!s}"


@mcp_app.tool()
async def scrape_outgoing_connections(max_results: int = 10) -> str:
    try:
        scraper = get_scraper()
        results = scraper.scrape_outgoing_connections(max_results)

        if results:
            return f"outgoing_connections:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        else:
            return "No outgoing connection requests found"

    except Exception as e:
        return f"Error scraping outgoing connections: {e!s}"


@mcp_app.tool()
async def scrape_company(company_url: str) -> str:
    if not company_url:
        raise ValueError("company_url is required")

    try:
        scraper = get_scraper()
        result = scraper.scrape_company(company_url)

        if result:
            return f"company_profile:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
        else:
            return f"Failed to scrape company: {company_url}"

    except Exception as e:
        return f"Error scraping company {company_url}: {e!s}"


@mcp_app.tool()
async def scrape_conversations_list(max_results: int = 10) -> str:
    try:
        scraper = get_scraper()
        conversations = scraper.scrape_conversations_list(max_results)

        if conversations:
            return f"conversations_list:\n{json.dumps(conversations, indent=2, ensure_ascii=False)}"
        else:
            return "No conversations found"

    except Exception as e:
        return f"Error scraping conversations list: {e!s}"


@mcp_app.tool()
async def scrape_conversation(participant_name: str | None = None) -> str:
    try:
        scraper = get_scraper()
        conversation_data = scraper.scrape_conversation_messages(participant_name)

        if conversation_data and conversation_data.get("messages"):
            return f"conversation:\n{json.dumps(conversation_data, indent=2, ensure_ascii=False)}"
        else:
            identifier = participant_name or "current"
            return f"No messages found for conversation: {identifier}"

    except Exception as e:
        return f"Error scraping conversation: {e!s}"


@mcp_app.tool()
async def send_connection_request(profile_url: str, note: str | None = None) -> str:
    if not profile_url:
        raise ValueError("profile_url is required")

    try:
        scraper = get_scraper()
        success = scraper.send_connection_request(profile_url, note)

        result = {
            "profile_url": profile_url,
            "note": note,
            "success": success,
            "message": "Connection request sent successfully"
            if success
            else "Failed to send connection request",
        }

        return f"connection_request_result:\n{json.dumps(result, indent=2, ensure_ascii=False)}"

    except Exception as e:
        return f"Error sending connection request to {profile_url}: {e!s}"


@cli_app.command
def serve(
    transport: Annotated[
        str,
        Parameter(
            name=["-t", "--transport"],
            help="Transport protocol for the server",
        ),
    ] = "stdio",
    host: Annotated[
        str,
        Parameter(
            name=["-h", "--host"],
            help="Host address for HTTP/SSE transport",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        Parameter(
            name=["-p", "--port"],
            help="Port number for HTTP/SSE transport",
        ),
    ] = 8000,
    email: Annotated[
        str | None,
        Parameter(help="LinkedIn email for authentication"),
    ] = None,
    password: Annotated[
        str | None,
        Parameter(help="LinkedIn password for authentication"),
    ] = None,
    cookie: Annotated[
        str | None,
        Parameter(help="LinkedIn li_at cookie for authentication"),
    ] = None,
    headless: Annotated[
        bool,
        Parameter(help="Run browser in headless mode"),
    ] = True,
    proxy: Annotated[
        str | None,
        Parameter(help="Proxy server (e.g., http://user:pass@host:port)"),
    ] = None,
):
    """Start the LinkedIn MCP server."""
    logger.info(f"Starting LinkedIn MCP {transport.upper()} Server...")

    try:
        logger.info("Initializing LinkedIn scraper...")
        _initialize_scraper(email, password, cookie, headless, proxy)
        logger.info("LinkedIn scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scraper: {e}")
        logger.error("Cannot start server without valid LinkedIn credentials")
        sys.exit(1)

    logger.info(
        f"FastMCP {transport.upper()} Server initialized with tools: scrape_profile, search_profiles, scrape_company, "
        "scrape_incoming_connections, scrape_outgoing_connections, scrape_conversations_list, "
        "scrape_conversation, send_connection_request, get_session_status, reset_session"
    )

    if transport in ["sse", "http", "streamable-http"]:
        logger.info(f"Starting {transport} server on {host}:{port}")
        mcp_app.run(transport=transport, host=host, port=port)
    elif transport == "stdio":
        logger.info("Starting stdio server")
        mcp_app.run(transport="stdio")
    else:
        logger.error(f"Unsupported transport: {transport}")
        logger.info("Supported transports: stdio, sse, http, streamable-http")
        sys.exit(1)


def _initialize_scraper(
    email: str | None = None,
    password: str | None = None,
    cookie: str | None = None,
    headless: bool = True,
    proxy: str | None = None,
) -> None:
    """Initialize the scraper with proper error handling."""
    global _scraper_instance

    if _scraper_instance is None:
        credentials = _get_credentials(email, password, cookie)
        proxy_server = proxy or os.getenv("PROXY_SERVER")
        config = ScraperConfig(headless=headless, proxy_server=proxy_server)

        _scraper_instance = LinkedinSpider(
            email=credentials.get("email"),
            password=credentials.get("password"),
            li_at_cookie=credentials.get("cookie"),
            config=config,
        )


def _get_credentials(email: str | None, password: str | None, cookie: str | None) -> dict:
    """Get authentication credentials from arguments or environment."""
    credentials = {
        "email": email or os.getenv("LINKEDIN_EMAIL"),
        "password": password or os.getenv("LINKEDIN_PASSWORD"),
        "cookie": cookie or os.getenv("LINKEDIN_COOKIE"),
    }

    return credentials


def cli_main():
    """CLI entry point."""
    cli_app()


def main():
    """Legacy main function for backward compatibility."""
    transport = "stdio"
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    if len(sys.argv) > 1:
        transport = sys.argv[1].lower()

    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    try:
        serve(transport=transport, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()