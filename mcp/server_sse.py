import json
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()


from fastmcp import FastMCP

from linkedin_scraper import LinkedInScraper, ScraperConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

app = FastMCP("linkedin-scraper")

_scraper_instance = None


def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")
        li_at_cookie = os.getenv("LINKEDIN_COOKIE")

        config = ScraperConfig()
        config.headless = os.getenv("HEADLESS", "true").lower() == "true"

        _scraper_instance = LinkedInScraper(
            email=email, password=password, li_at_cookie=li_at_cookie, config=config
        )

    return _scraper_instance


@app.tool()
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


@app.tool()
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


@app.tool()
async def get_session_status() -> str:
    try:
        scraper = get_scraper()
        is_active = scraper.keep_alive()
        status = "Active" if is_active else "Inactive"
        return f"LinkedIn browser session status: {status}"

    except Exception as e:
        return f"Error checking session status: {e!s}"


@app.tool()
async def reset_session() -> str:
    global _scraper_instance
    try:
        if _scraper_instance:
            _scraper_instance.close()
            _scraper_instance = None
        return "LinkedIn browser session has been reset successfully"

    except Exception as e:
        return f"Error resetting session: {e!s}"


@app.tool()
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


@app.tool()
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


@app.tool()
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


@app.tool()
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


@app.tool()
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


@app.tool()
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


def main():
    logger.info("Starting LinkedIn MCP SSE Server...")

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    try:
        logger.info("Initializing LinkedIn scraper...")
        get_scraper()
        logger.info("LinkedIn scraper initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize scraper: {e}")
        logger.info("Server will start but scraper will be inactive")

    logger.info(
        "FastMCP SSE Server initialized with tools: scrape_profile, search_profiles, scrape_company, scrape_incoming_connections, scrape_outgoing_connections, scrape_conversations_list, scrape_conversation, send_connection_request, get_session_status, reset_session"
    )
    logger.info("Server is ready and waiting for SSE connections...")

    logger.info(f"Starting server on {host}:{port}")
    app.run(transport="sse", host=host, port=port)


def sse_main():
    main()


if __name__ == "__main__":
    sse_main()
