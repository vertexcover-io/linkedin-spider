# linkedin-spider

A modern LinkedIn scraping library with built-in anti-detection, available as a Python library, CLI tool, and [MCP](https://modelcontextprotocol.io/) server.

[![PyPI](https://img.shields.io/pypi/v/linkedin-spider?style=flat-square)](https://pypi.org/project/linkedin-spider/)
[![Python](https://img.shields.io/pypi/pyversions/linkedin-spider?style=flat-square)](https://pypi.org/project/linkedin-spider/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Docker](https://img.shields.io/docker/v/vertexcoverlabs/linkedin-mcp?label=Docker&style=flat-square)](https://hub.docker.com/r/vertexcoverlabs/linkedin-mcp)

[MCP Server](#mcp-server) · [Python Library](#python-library) · [CLI](#command-line-interface) · [Docker](#docker)

## Features

- **Profile search** with advanced filters (location, industry, company, connection degree)
- **Post search** by keywords with engagement metrics and comments
- **Profile scraping** with experience, education, skills, and contact details
- **Company scraping** with industry, size, specialties, and more
- **Connection management** — retrieve and send connection requests
- **Conversations** — list threads and read message history
- **Proxy support** — route traffic through HTTP or SOCKS5 proxies
- **Anti-detection** — human-like behavior simulation, stealth mode, session persistence

## Installation

```bash
pip install linkedin-spider        # library only
pip install linkedin-spider[cli]   # library + CLI
pip install linkedin-spider[mcp]   # library + MCP server
pip install linkedin-spider[all]   # everything
```

## Authentication

linkedin-spider supports two authentication methods. Sessions are persisted in a Chrome profile so you typically only authenticate once.

**LinkedIn Cookie (Recommended)**

1. Log in to LinkedIn in your browser
2. Open DevTools (F12) → Application → Cookies → `linkedin.com`
3. Copy the `li_at` cookie value

```python
scraper = LinkedinSpider(li_at_cookie="your_cookie_value")
```

**Email & Password**

```python
scraper = LinkedinSpider(email="you@example.com", password="your_password")
```

For CLI and MCP, pass `--cookie` (or `--email`/`--password`) flags, or set the `LINKEDIN_COOKIE` (or `LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD`) environment variables.

## MCP Server

The MCP server exposes LinkedIn data to AI assistants like Claude.

**Example prompts you can give Claude once connected:**

```
Research the background of this candidate https://www.linkedin.com/in/johndoe
```

```
Find 10 product managers in San Francisco and summarize their experience
```

```
What has OpenAI been posting about recently? https://www.linkedin.com/company/openai
```

```
Show me my pending connection requests and summarize who they are
```

It provides 11 tools:

| Tool                          | Description                                                             |
| ----------------------------- | ----------------------------------------------------------------------- |
| `search_profiles`             | Search profiles with filters (location, industry, company, connections) |
| `scrape_profile`              | Extract complete profile data from a URL                                |
| `search_posts`                | Search posts by keywords with date filters                              |
| `scrape_company`              | Get company details from a URL                                          |
| `scrape_incoming_connections` | List pending connection requests received                               |
| `scrape_outgoing_connections` | List connection requests you've sent                                    |
| `send_connection_request`     | Send a connection request with optional note                            |
| `scrape_conversations_list`   | List messaging conversations                                            |
| `scrape_conversation`         | Read messages from a conversation                                       |
| `get_session_status`          | Check if the browser session is active                                  |
| `reset_session`               | Close and reset the browser session                                     |

### Start the server

```bash
# stdio (default — for Claude Desktop, Claude Code)
linkedin-spider-mcp serve --cookie your_li_at_cookie_value

# SSE or HTTP (for remote clients)
linkedin-spider-mcp serve --transport sse --host 127.0.0.1 --port 8000
linkedin-spider-mcp serve --transport http --host 0.0.0.0 --port 9000
```

Or configure via environment variables in a `.env` file:

```env
LINKEDIN_COOKIE=your_li_at_cookie_value
HEADLESS=true
PROXY_URL=http://host:port          # optional
```

### Claude Desktop

Add to your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### With Docker (Recommended)

No local dependencies required — the Docker image includes Python, Chrome, and everything needed.

```json
{
  "mcpServers": {
    "linkedin-spider": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "LINKEDIN_COOKIE=your_li_at_cookie_value",
        "-e",
        "HEADLESS=true",
        "-e",
        "TRANSPORT=stdio",
        "vertexcoverlabs/linkedin-mcp"
      ]
    }
  }
}
```

#### Without Docker

Requires `pip install linkedin-spider[mcp]` and Chrome installed locally.

```json
{
  "mcpServers": {
    "linkedin-spider": {
      "command": "linkedin-spider-mcp",
      "args": ["serve", "--cookie", "your_li_at_cookie_value"]
    }
  }
}
```

### Claude Code

#### With Docker

```bash
claude mcp add linkedin-spider -- \
  docker run --rm -i \
  -e LINKEDIN_COOKIE=your_li_at_cookie_value \
  -e HEADLESS=true \
  -e TRANSPORT=stdio \
  vertexcoverlabs/linkedin-mcp
```

#### Without Docker

```bash
claude mcp add linkedin-spider -- \
  linkedin-spider-mcp serve --cookie your_li_at_cookie_value
```

Or connect to a running SSE/HTTP server:

```bash
claude mcp add linkedin-spider --transport sse http://localhost:8000/sse
```

### Troubleshooting

<details>
<summary><b>Authentication issues</b></summary>

- **Cookie expired:** LinkedIn cookies expire periodically. Grab a fresh `li_at` value from your browser.
- **Email/password not working:** LinkedIn may trigger a CAPTCHA or verification. Try cookie auth instead.
- **Session reuse:** Sessions are saved in a Chrome profile. If things break, delete the profile directory and re-authenticate.

</details>

<details>
<summary><b>Docker issues</b></summary>

- **First-time pull is slow:** The image is ~1.4GB. Pre-pull with `docker pull vertexcoverlabs/linkedin-mcp` before configuring Claude Desktop to avoid timeout.
- **Port conflicts:** If port 8080 is in use, map to a different host port: `-p 9090:8080`.

</details>

<details>
<summary><b>Browser / Chrome issues</b></summary>

- **Chrome not found (non-Docker):** Set `CHROMEDRIVER_PATH` in your `.env` or pass `chromedriver_path` in `ScraperConfig`.
- **Page load timeouts:** Increase `page_load_timeout` in `ScraperConfig` or use a faster proxy.
- **Headless mode issues:** Some LinkedIn pages behave differently in headless mode. Try `headless=False` for debugging.

</details>

## Python Library

```python
from linkedin_spider import LinkedinSpider, ScraperConfig

config = ScraperConfig(headless=True, page_load_timeout=30)
scraper = LinkedinSpider(
    li_at_cookie="your_cookie_value",
    config=config,
)

# Search profiles
results = scraper.search_profiles("software engineer", max_results=10)

# Search posts
posts = scraper.search_posts("artificial intelligence", max_results=10)

# Scrape a single profile
profile = scraper.scrape_profile("https://linkedin.com/in/someone")

# Scrape a company page
company = scraper.scrape_company("https://linkedin.com/company/openai")

# Connection requests
incoming = scraper.scrape_incoming_connections(max_results=20)
scraper.send_connection_request("https://linkedin.com/in/someone", note="Hi!")

# Conversations
threads = scraper.scrape_conversations_list(max_results=10)
messages = scraper.scrape_conversation_messages("John Doe")

# Always clean up
scraper.close()
```

See the [examples/](./examples) directory for more detailed usage.

### Configuration

`ScraperConfig` accepts the following options:

| Option              | Default      | Description                          |
| ------------------- | ------------ | ------------------------------------ |
| `headless`          | `False`      | Run browser without a visible window |
| `stealth_mode`      | `True`       | Inject anti-detection scripts        |
| `page_load_timeout` | `30`         | Page load timeout in seconds         |
| `implicit_wait`     | `10`         | Implicit wait timeout in seconds     |
| `human_delay_range` | `(0.5, 2.0)` | Random delay range between actions   |
| `proxy`             | `None`       | Proxy URL (`http://` or `socks5://`) |
| `custom_user_agent` | `None`       | Override the default user agent      |

## Command Line Interface

```bash
# Search profiles
linkedin-spider-cli search -q "product manager" -n 10 -o results.json

# Search posts
linkedin-spider-cli search-posts -k "artificial intelligence" -n 10 -o posts.json

# Scrape a profile
linkedin-spider-cli profile -u "https://linkedin.com/in/johndoe" -o profile.json

# Scrape a company
linkedin-spider-cli company -u "https://linkedin.com/company/openai" -o company.json

# List connection requests
linkedin-spider-cli connections -n 20 -o connections.json
```

Pass `--cookie` on first use (or set `LINKEDIN_COOKIE` env var). You can also use `--email`/`--password` instead. The session is saved and reused for subsequent commands.

Output defaults to stdout. Use `-o` to write JSON or CSV files.

## Docker

A pre-built Docker image is published on [Docker Hub](https://hub.docker.com/r/vertexcoverlabs/linkedin-mcp):

```bash
docker pull vertexcoverlabs/linkedin-mcp
```

Or build locally:

```bash
docker build -t linkedin-spider .
```

Run with different transports:

```bash
# stdio
docker run --rm -i -e TRANSPORT=stdio --env-file .env vertexcoverlabs/linkedin-mcp

# SSE
docker run -p 8080:8080 -e TRANSPORT=sse --env-file .env vertexcoverlabs/linkedin-mcp

# HTTP
docker run -p 8080:8080 -e TRANSPORT=http --env-file .env vertexcoverlabs/linkedin-mcp
```

## Running in the Cloud

LinkedIn blocks requests from known datacenter IP ranges. To run linkedin-spider on a cloud server (AWS, GCP, Azure, etc.), route browser traffic through a residential or mobile proxy using the `PROXY_URL` environment variable.

```env
LINKEDIN_COOKIE=your_li_at_cookie_value
HEADLESS=true
PROXY_URL=http://user:pass@proxy-host:port
```

Both HTTP and SOCKS5 proxies are supported:

```env
PROXY_URL=http://user:pass@proxy-host:port
PROXY_URL=socks5://user:pass@proxy-host:port
```

When using Docker, pass it as an environment variable:

```bash
docker run --rm -i \
  -e LINKEDIN_COOKIE=your_li_at_cookie_value \
  -e PROXY_URL=http://user:pass@proxy-host:port \
  -e HEADLESS=true \
  -e TRANSPORT=stdio \
  vertexcoverlabs/linkedin-mcp
```

When using the Python library, pass it via `ScraperConfig`:

```python
config = ScraperConfig(headless=True, proxy="http://user:pass@proxy-host:port")
```

> [!TIP]
> Residential proxies are recommended over datacenter proxies to avoid detection.

## Development

```bash
git clone https://github.com/vertexcover-io/linkedin-spider
cd linkedin-spider
uv sync
cp .env.example .env   # add your credentials
```

```bash
make check    # lint + typecheck
make test     # run tests
make build    # build wheel
```

## Disclaimer

This tool is for personal and educational use. Please respect LinkedIn's Terms of Service, use reasonable rate limits, and handle collected data responsibly.
