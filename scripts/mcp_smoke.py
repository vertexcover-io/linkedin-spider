"""Subprocess MCP smoke test.

Spawns `linkedin-spider-mcp` over stdio, drives it as a real MCP client, and
asserts the JSON-RPC stream stays clean (no rogue chromedriver / Python output
on stdout). Catches the exact failure class that broke MCP after the v0.3.x
release ("Unexpected token 's', \"self.confi\"... is not valid JSON").

Run:  uv run python scripts/mcp_smoke.py

Exits 0 on success, non-zero on any leak / handshake / tool-call failure.
On failure, prints the server's stderr so we can see why init died.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


async def run_probe() -> int:
    cookie = os.environ.get("LINKEDIN_COOKIE")
    if not cookie:
        print("ERROR: LINKEDIN_COOKIE not set — MCP server needs it to init.", file=sys.stderr)
        return 2

    params = StdioServerParameters(
        command="uv",
        args=["run", "linkedin-spider-mcp", "serve", "--transport", "stdio"],
        env={**os.environ, "LINKEDIN_COOKIE": cookie},
        cwd=str(REPO_ROOT),
    )

    # Capture the server's stderr to a file so we can show it on failure.
    with tempfile.NamedTemporaryFile(
        mode="w+", prefix="mcp-smoke-stderr-", suffix=".log", delete=False
    ) as stderr_file:
        print(f"→ Server stderr → {stderr_file.name}", file=sys.stderr)
        try:
            async with (
                stdio_client(params, errlog=stderr_file) as (read, write),
                ClientSession(read, write) as session,
            ):
                print("→ Initializing JSON-RPC session...", file=sys.stderr)
                await asyncio.wait_for(session.initialize(), timeout=180)

                print("→ Listing tools...", file=sys.stderr)
                tools_result = await session.list_tools()
                names = sorted(t.name for t in tools_result.tools)
                print(f"   got {len(names)} tools: {', '.join(names[:5])}...", file=sys.stderr)
                assert "get_session_status" in names, f"expected get_session_status, got {names}"

                print("→ Calling get_session_status...", file=sys.stderr)
                result = await session.call_tool("get_session_status", {})
                preview = str(result.content)[:200] if result.content else "<no content>"
                print(f"   result preview: {preview}", file=sys.stderr)
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            stderr_file.seek(0)
            captured = stderr_file.read()
            print("\n── server stderr ──", file=sys.stderr)
            print(captured[-4000:] if len(captured) > 4000 else captured, file=sys.stderr)
            return 1
        else:
            print("✓ MCP stdio handshake + tool call succeeded.", file=sys.stderr)
            return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run_probe()))
