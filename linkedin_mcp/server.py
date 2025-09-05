import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.server import Server
from mcp import McpError
import mcp.server.stdio

from .core.session_manager import LinkedInSessionManager
from .scrapers.search_filters import SearchFilters

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Server("linkedin-scraper")

session_manager = LinkedInSessionManager()

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="scrape_profile",
            description="Scrape a single LinkedIn profile by URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "profile_url": {
                        "type": "string",
                        "description": "The LinkedIn profile URL to scrape"
                    }
                },
                "required": ["profile_url"]
            }
        ),
        types.Tool(
            name="search_profiles",
            description="Search and scrape LinkedIn profiles based on query and filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for finding profiles"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of profiles to scrape (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "location": {
                        "type": "string",
                        "description": "Location filter for the search (optional)"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry filter for the search (optional)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_session_status",
            description="Check the status of the LinkedIn browser session",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="reset_session",
            description="Reset the LinkedIn browser session (closes and reopens browser)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    try:
        if name == "scrape_profile":
            return await scrape_profile_tool(arguments or {})
        elif name == "search_profiles":
            return await search_profiles_tool(arguments or {})
        elif name == "get_session_status":
            return await get_session_status_tool()
        elif name == "reset_session":
            return await reset_session_tool()
        else:
            raise McpError(-32601, f"Unknown tool: {name}")
    except Exception as e:
        raise McpError(-32603, str(e))

async def scrape_profile_tool(arguments: Dict[str, Any]) -> List[types.TextContent]:
    profile_url = arguments.get("profile_url")
    
    if not profile_url:
        raise McpError(-32602, "profile_url is required")
    
    try:
        scraper = session_manager.get_scraper()
        result = scraper.scrape_profile(profile_url)
        
        if result:
            return [types.TextContent(
                type="text",
                text=f"{json.dumps(result, indent=2, ensure_ascii=False)}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to scrape profile: {profile_url}"
            )]
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error scraping profile {profile_url}: {str(e)}"
        )]

async def search_profiles_tool(arguments: Dict[str, Any]) -> List[types.TextContent]:
    query = arguments.get("query")
    max_results = arguments.get("max_results", 5)
    location = arguments.get("location")
    industry = arguments.get("industry")
    
    if not query:
        raise McpError(-32602, "query is required")
    
    try:
        scraper = session_manager.get_scraper()
        
        filters = None
        if location or industry:
            filters = SearchFilters(location=location, industry=industry)
        
        results = scraper.scrape_search_results(query, max_results, filters)
        
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
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error searching profiles for '{query}': {str(e)}"
        )]

async def get_session_status_tool() -> List[types.TextContent]:
    try:
        is_active = session_manager.is_session_active()
        status = "Active" if is_active else "Inactive"
        
        return [types.TextContent(
            type="text",
            text=f"LinkedIn browser session status: {status}"
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error checking session status: {str(e)}"
        )]

async def reset_session_tool() -> List[types.TextContent]:
    try:
        session_manager.reset_session()
        return [types.TextContent(
            type="text",
            text="LinkedIn browser session has been reset successfully"
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error resetting session: {str(e)}"
        )]

async def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    logger.info("Starting LinkedIn MCP Server...")
    
    logger.info("Initializing LinkedIn browser session...")
    try:
        session_manager.initialize_session()
        logger.info("LinkedIn browser session initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize browser session: {e}")
        logger.info("Server will start but browser session will be inactive")
    
    initialization_options = mcp.server.InitializationOptions(
        server_name="linkedin-scraper",
        server_version="1.0.0",
        capabilities=mcp.types.ServerCapabilities(
            tools={}
        )
    )
    
    logger.info("MCP Server initialized with tools: scrape_profile, search_profiles, get_session_status, reset_session")
    logger.info("Server is ready and waiting for client connections...")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server is now running and listening for client connections")
        await app.run(read_stream, write_stream, initialization_options)

def cli_main():
    asyncio.run(main())

if __name__ == "__main__":
    cli_main()