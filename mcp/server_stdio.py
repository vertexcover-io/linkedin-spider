import asyncio
import json
import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

load_dotenv()

from linkedin_scraper import LinkedInScraper, ScraperConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

server = Server("linkedin-scraper")

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


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="scrape_profile",
            description="Scrape LinkedIn profile information",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_url": {
                        "type": "string",
                        "description": "LinkedIn profile URL to scrape"
                    }
                },
                "required": ["profile_url"]
            },
        ),
        types.Tool(
            name="search_profiles",
            description="Search LinkedIn profiles with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for profiles"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "location": {
                        "type": "string",
                        "description": "Location filter"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry filter"
                    },
                    "current_company": {
                        "type": "string",
                        "description": "Current company filter"
                    },
                    "connections": {
                        "type": "string",
                        "description": "Connections filter"
                    },
                    "connection_of": {
                        "type": "string",
                        "description": "Connection of filter"
                    },
                    "followers_of": {
                        "type": "string",
                        "description": "Followers of filter"
                    }
                },
                "required": ["query"]
            },
        ),
        types.Tool(
            name="get_session_status",
            description="Check LinkedIn browser session status",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        ),
        types.Tool(
            name="reset_session",
            description="Reset LinkedIn browser session",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        ),
        types.Tool(
            name="scrape_incoming_connections",
            description="Scrape incoming connection requests",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                }
            },
        ),
        types.Tool(
            name="scrape_outgoing_connections",
            description="Scrape outgoing connection requests",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                }
            },
        ),
        types.Tool(
            name="scrape_company",
            description="Scrape LinkedIn company information",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_url": {
                        "type": "string",
                        "description": "LinkedIn company URL to scrape"
                    }
                },
                "required": ["company_url"]
            },
        ),
        types.Tool(
            name="scrape_conversations_list",
            description="Scrape list of LinkedIn conversations",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of conversations to return",
                        "default": 10
                    }
                }
            },
        ),
        types.Tool(
            name="scrape_conversation",
            description="Scrape messages from a LinkedIn conversation",
            inputSchema={
                "type": "object",
                "properties": {
                    "participant_name": {
                        "type": "string",
                        "description": "Name of the conversation participant"
                    }
                }
            },
        ),
        types.Tool(
            name="send_connection_request",
            description="Send a LinkedIn connection request",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_url": {
                        "type": "string",
                        "description": "LinkedIn profile URL to send connection request to"
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note to include with the connection request"
                    }
                },
                "required": ["profile_url"]
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if arguments is None:
        arguments = {}

    try:
        if name == "scrape_profile":
            profile_url = arguments.get("profile_url")
            if not profile_url:
                raise ValueError("profile_url is required")

            scraper = get_scraper()
            result = scraper.scrape_profile(profile_url)

            if result:
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Failed to scrape profile: {profile_url}"
                )]

        elif name == "search_profiles":
            query = arguments.get("query")
            if not query:
                raise ValueError("query is required")

            max_results = arguments.get("max_results", 5)
            location = arguments.get("location")
            industry = arguments.get("industry")
            current_company = arguments.get("current_company")
            connections = arguments.get("connections")
            connection_of = arguments.get("connection_of")
            followers_of = arguments.get("followers_of")

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
                return [types.TextContent(
                    type="text",
                    text=f"profiles:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"No profiles found for query: {query}"
                )]

        elif name == "get_session_status":
            scraper = get_scraper()
            is_active = scraper.keep_alive()
            status = "Active" if is_active else "Inactive"
            return [types.TextContent(
                type="text",
                text=f"LinkedIn browser session status: {status}"
            )]

        elif name == "reset_session":
            global _scraper_instance
            if _scraper_instance:
                _scraper_instance.close()
                _scraper_instance = None
            return [types.TextContent(
                type="text",
                text="LinkedIn browser session has been reset successfully"
            )]

        elif name == "scrape_incoming_connections":
            max_results = arguments.get("max_results", 10)
            scraper = get_scraper()
            results = scraper.scrape_incoming_connections(max_results)

            if results:
                return [types.TextContent(
                    type="text",
                    text=f"incoming_connections:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No incoming connection requests found"
                )]

        elif name == "scrape_outgoing_connections":
            max_results = arguments.get("max_results", 10)
            scraper = get_scraper()
            results = scraper.scrape_outgoing_connections(max_results)

            if results:
                return [types.TextContent(
                    type="text",
                    text=f"outgoing_connections:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No outgoing connection requests found"
                )]

        elif name == "scrape_company":
            company_url = arguments.get("company_url")
            if not company_url:
                raise ValueError("company_url is required")

            scraper = get_scraper()
            result = scraper.scrape_company(company_url)

            if result:
                return [types.TextContent(
                    type="text",
                    text=f"company_profile:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Failed to scrape company: {company_url}"
                )]

        elif name == "scrape_conversations_list":
            max_results = arguments.get("max_results", 10)
            scraper = get_scraper()
            conversations = scraper.scrape_conversations_list(max_results)

            if conversations:
                return [types.TextContent(
                    type="text",
                    text=f"conversations_list:\n{json.dumps(conversations, indent=2, ensure_ascii=False)}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="No conversations found"
                )]

        elif name == "scrape_conversation":
            participant_name = arguments.get("participant_name")
            scraper = get_scraper()
            conversation_data = scraper.scrape_conversation_messages(participant_name)

            if conversation_data and conversation_data.get("messages"):
                return [types.TextContent(
                    type="text",
                    text=f"conversation:\n{json.dumps(conversation_data, indent=2, ensure_ascii=False)}"
                )]
            else:
                identifier = participant_name or "current"
                return [types.TextContent(
                    type="text",
                    text=f"No messages found for conversation: {identifier}"
                )]

        elif name == "send_connection_request":
            profile_url = arguments.get("profile_url")
            if not profile_url:
                raise ValueError("profile_url is required")

            note = arguments.get("note")
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

            return [types.TextContent(
                type="text",
                text=f"connection_request_result:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
            )]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error in {name}: {e!s}"
        )]


async def main():
    logger.info("Starting LinkedIn MCP STDIO Server...")

    try:
        logger.info("Initializing LinkedIn scraper...")
        get_scraper()
        logger.info("LinkedIn scraper initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize scraper: {e}")
        logger.info("Server will start but scraper will be inactive")

    logger.info(
        "MCP STDIO Server initialized with tools: scrape_profile, search_profiles, scrape_company, scrape_incoming_connections, scrape_outgoing_connections, scrape_conversations_list, scrape_conversation, send_connection_request, get_session_status, reset_session"
    )

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="linkedin-scraper",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def cli_main():
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()