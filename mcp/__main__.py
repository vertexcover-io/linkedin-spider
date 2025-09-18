"""Allow running the MCP server module directly with python -m linkedin_scraper_mcp."""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        from .server_sse import sse_main

        sse_main()
