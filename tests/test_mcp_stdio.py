"""Subprocess MCP stdio test.

Spawns the real `linkedin-spider-mcp serve --transport stdio` binary, drives
it as a JSON-RPC client over stdio, and asserts the handshake + a cheap tool
call succeed without any non-JSON corruption on stdout.

Catches stdout-leak regressions that the in-memory tests in test_mcp_server.py
cannot — for example:
  - chromedriver subprocess output (Service log_output=None)
  - cyclopts help/error panels rendered to stdout
  - stray print()s in the scraper path

Lives in its own file so it doesn't collide on the Chrome profile dir with the
session-scoped `spider` fixture used elsewhere — Chrome would lock
~/.linkedin_spider_profiles/default_profile/ otherwise. Run as:

    uv run pytest tests/test_mcp_stdio.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import TextIO, cast

import pytest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.integration
async def test_mcp_stdio_handshake_and_tool_call() -> None:
    """Real subprocess MCP client: handshake → list_tools → call get_session_status."""
    cookie = os.environ.get("LINKEDIN_COOKIE")
    if not cookie:
        pytest.skip("LINKEDIN_COOKIE not set — MCP server needs it to init")

    params = StdioServerParameters(
        command="uv",
        args=["run", "linkedin-spider-mcp", "serve", "--transport", "stdio"],
        env={**os.environ, "LINKEDIN_COOKIE": cookie},
        cwd=str(REPO_ROOT),
    )

    # Capture the server's stderr to a temp file so pytest's failure report
    # shows why init died if it does.
    with tempfile.NamedTemporaryFile(
        mode="w+", prefix="mcp-stdio-stderr-", suffix=".log", delete=False
    ) as stderr_file:
        try:
            async with (
                stdio_client(params, errlog=cast("TextIO", stderr_file)) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()

                tools_result = await session.list_tools()
                names = {t.name for t in tools_result.tools}
                assert "get_session_status" in names, (
                    f"missing get_session_status; got {sorted(names)}"
                )

                result = await session.call_tool("get_session_status", {})
                assert result.content, "get_session_status returned empty content"
                text = str(result.content)
                assert "Active" in text, f"expected 'Active' in result, got: {text[:200]}"
        except Exception:
            stderr_file.seek(0)
            captured = stderr_file.read()
            print(
                f"\n── server stderr ({stderr_file.name}) ──\n"
                f"{captured[-4000:] if len(captured) > 4000 else captured}",
                file=sys.stderr,
            )
            raise
