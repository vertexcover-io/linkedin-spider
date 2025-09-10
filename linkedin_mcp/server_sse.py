import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
import mcp.types as types
from mcp import McpError

from .core.session_manager import LinkedInSessionManager
from .scrapers.search_filters import SearchFilters

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastMCP("linkedin-scraper")

session_manager = LinkedInSessionManager()

@app.tool()
async def scrape_profile(profile_url: str) -> str:
    if not profile_url:
        raise ValueError("profile_url is required")
    
    try:
        scraper = session_manager.get_scraper()
        result = scraper.scrape_profile(profile_url)
        
        if result:
            return json.dumps(result, indent=2, ensure_ascii=False)
        else:
            return f"Failed to scrape profile: {profile_url}"
            
    except Exception as e:
        return f"Error scraping profile {profile_url}: {str(e)}"

@app.tool()
async def search_profiles(
    query: str,
    max_results: int = 5,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    current_company: Optional[str] = None,
    connections: Optional[str] = None,
    connection_of: Optional[str] = None,
    followers_of: Optional[str] = None
) -> str:
    if not query:
        raise ValueError("query is required")
    
    try:
        scraper = session_manager.get_scraper()
        
        filters = None
        if location or industry or current_company or connections or connection_of or followers_of:
            filters = SearchFilters(
                location=location,
                industry=industry,
                current_company=current_company,
                connections=connections,
                connection_of=connection_of,
                followers_of=followers_of
            )
        
        results = scraper.scrape_search_results(query, max_results, filters)
        
        if results:
            return f"profiles:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        else:
            return f"No profiles found for query: {query}"
            
    except Exception as e:
        return f"Error searching profiles for '{query}': {str(e)}"

@app.tool()
async def get_session_status() -> str:
    try:
        is_active = session_manager.is_session_active()
        status = "Active" if is_active else "Inactive"
        return f"LinkedIn browser session status: {status}"
        
    except Exception as e:
        return f"Error checking session status: {str(e)}"

@app.tool()
async def reset_session() -> str:
    try:
        session_manager.reset_session()
        return "LinkedIn browser session has been reset successfully"
        
    except Exception as e:
        return f"Error resetting session: {str(e)}"

@app.tool()
async def scrape_incoming_connections(max_results: int = 10) -> str:
    try:
        scraper = session_manager.get_scraper()
        results = scraper.scrape_incoming_connections(max_results)
        
        if results:
            return f"incoming_connections:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        else:
            return "No incoming connection requests found"
            
    except Exception as e:
        return f"Error scraping incoming connections: {str(e)}"

@app.tool()
async def scrape_outgoing_connections(max_results: int = 10) -> str:
    try:
        scraper = session_manager.get_scraper()
        results = scraper.scrape_outgoing_connections(max_results)
        
        if results:
            return f"outgoing_connections:\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        else:
            return "No outgoing connection requests found"
            
    except Exception as e:
        return f"Error scraping outgoing connections: {str(e)}"

@app.tool()
async def scrape_company(company_url: str) -> str:
    if not company_url:
        raise ValueError("company_url is required")
    
    try:
        scraper = session_manager.get_scraper()
        result = scraper.scrape_company(company_url)
        
        if result:
            return f"company_profile:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
        else:
            return f"Failed to scrape company: {company_url}"
            
    except Exception as e:
        return f"Error scraping company {company_url}: {str(e)}"

@app.tool()
async def scrape_conversations_list(max_results: int = 10) -> str:
    try:
        scraper = session_manager.get_scraper()
        conversations = scraper.scrape_conversations_list(max_results)
        
        if conversations:
            return f"conversations_list:\n{json.dumps(conversations, indent=2, ensure_ascii=False)}"
        else:
            return "No conversations found"
            
    except Exception as e:
        return f"Error scraping conversations list: {str(e)}"

@app.tool()
async def scrape_conversation(participant_name: Optional[str] = None) -> str:
    try:
        scraper = session_manager.get_scraper()
        conversation_data = scraper.scrape_conversation_messages(participant_name)
        
        if conversation_data and conversation_data.get('messages'):
            return f"conversation:\n{json.dumps(conversation_data, indent=2, ensure_ascii=False)}"
        else:
            identifier = participant_name or 'current'
            return f"No messages found for conversation: {identifier}"
            
    except Exception as e:
        return f"Error scraping conversation: {str(e)}"

def main():
    from dotenv import load_dotenv
    load_dotenv()
    
    logger.info("Starting LinkedIn MCP SSE Server...")
    
    logger.info("Initializing LinkedIn browser session...")
    try:
        session_manager.initialize_session()
        logger.info("LinkedIn browser session initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize browser session: {e}")
        logger.info("Server will start but browser session will be inactive")
    
    logger.info("FastMCP SSE Server initialized with tools: scrape_profile, search_profiles, scrape_company, scrape_incoming_connections, scrape_outgoing_connections, get_session_status, reset_session")
    logger.info("Server is ready and waiting for SSE connections...")
    
    app.run(transport="sse")

def cli_main():
    main()

if __name__ == "__main__":
    cli_main()