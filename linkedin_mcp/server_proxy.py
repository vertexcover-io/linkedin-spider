import asyncio
import logging
from fastmcp import FastMCP
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_stdio_to_sse_proxy():
    from dotenv import load_dotenv
    load_dotenv()
    
    logger.info("Creating LinkedIn MCP Proxy Server (stdio to SSE)...")
    
    proxy_client = Client(
        transport=PythonStdioTransport(
            command="python",
            args=["-m", "linkedin_mcp.server"],
            cwd="D:\\vertexcover\\linkedin_scraper"
        )
    )
    
    proxy = FastMCP.as_proxy(
        proxy_client, 
        name="LinkedIn MCP Proxy (stdio->SSE)"
    )
    
    logger.info("Proxy server created successfully")
    logger.info("Starting SSE transport for proxy server...")
    
    await proxy.run(transport="sse")

def cli_main():
    asyncio.run(create_stdio_to_sse_proxy())

if __name__ == "__main__":
    cli_main()