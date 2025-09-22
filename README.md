# linkedin-scraper-mcp

Effortless LinkedIn scraping with zero detection. Extract, export, and automate your LinkedIn data.

## Features

- Search LinkedIn profiles with advanced filters (location, connection type, current company, position)
- Extract complete profile information (experience, education, skills, contact details)
- Get company details and information
- Retrieve incoming and outgoing connection requests
- Send connection requests to profiles
- Get conversations list and detailed conversation history
- Built-in anti-detection and session management

## Quick Start

### Installation

```bash
# Install with uv
uv sync
```

## Different ways to use it

### 1. Python Library

Perfect for integration into your existing Python applications:

```python
from linkedin_scraper import LinkedInScraper, ScraperConfig

config = ScraperConfig(headless=True, page_load_timeout=30)

# Authenticate (use either email/password or cookie).
# NOTE: cookie method is still under beta so use email/password for auth
# Authentication is mostly done once and the session is saved in the chrome profile
scraper = LinkedInScraper(
    email="your_email@example.com",
    password="your_password",
    config=config
)

results = scraper.search_profiles("software engineer", max_results=10)
profile = scraper.scrape_profile("https://linkedin.com/in/someone")
company = scraper.scrape_company("https://linkedin.com/company/tech-corp")

# Don't forget to clean up
scraper.close()
```

For more examples : [examples](./examples)

### 2. Command Line Interface

Great for quick data extraction and scripting:

```bash
uv run linkedin_scraper_cli search -q "product manager" -n 10 -o results.json
uv run linkedin_scraper_cli profile -u "https://linkedin.com/in/johndoe" -o profile.json
uv run linkedin_scraper_cli company -u "https://linkedin.com/company/openai" -o company.json
```

### 3. MCP Server

Set up environment variables in `.env` file:

```env
# Authentication (choose one method)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
# OR
LINKEDIN_COOKIE=your_li_at_cookie_value

# Configuration
HEADLESS=true
```

Start the MCP server:

```bash
uv run linkedin_scraper_mcp
# Copy the server url to use
```

#### Claude Code Integration

```bash
# Add to Claude Code
claude mcp add linkedin-scraper --transport sse <server-url> 
# Example server URL format: http://localhost:8080/sse
```

#### Claude Desktop Integration

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

##### Option 1: Docker (Recommended)

The Docker approach provides reliable, isolated execution with all dependencies included.

First, build the Docker image:
```bash
# Build the stdio server image
docker build -f Dockerfile.stdio -t linkedin-mcp-stdio .
```

Then add this to your Claude Desktop configuration:
```json
{
  "mcpServers": {
    "linkedin-scraper": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "LINKEDIN_EMAIL=your_email@example.com",
        "-e", "LINKEDIN_PASSWORD=your_password",
        "-e", "HEADLESS=true",
        "linkedin-mcp-stdio"
      ]
    }
  }
}
```

##### Option 2: Direct Installation (Alternative)

If you prefer not to use Docker, you can install directly:

```bash
# Install globally
uv tool install --editable .
```

Then configure Claude Desktop:
```json
{
  "mcpServers": {
    "linkedin-scraper": {
      "command": "linkedin_scraper_std",
      "env": {
        "LINKEDIN_EMAIL": "your_email@example.com",
        "LINKEDIN_PASSWORD": "your_password",
        "HEADLESS": "true"
      }
    }
  }
}
```



### 4. Docker for Development & Testing

If you want to run the SSE server or test the application in Docker:

#### SSE Server
```bash
# Build and run SSE server
docker build -t linkedin-mcp-sse .
docker run -p 8080:8080 --env-file .env linkedin-mcp-sse
```

#### STDIO Server
```bash
docker build -f Dockerfile.stdio -t linkedin-mcp-stdio .
docker run --rm -i --env-file .env linkedin-mcp-stdio
```


## Authentication Methods

### Method 1: LinkedIn Cookie

1. Login to LinkedIn in your browser
2. Open Developer Tools (F12)
3. Go to Application/Storage → Cookies → linkedin.com
4. Copy the `li_at` cookie value
5. Use it in your code:

```python
scraper = LinkedInScraper(li_at_cookie="your_cookie_value")
```

### Method 2: Email & Password (Recommended)

```python
scraper = LinkedInScraper(
    email="your_email@example.com",
    password="your_password"
)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for personal use only. Please:

- Respect LinkedIn's Terms of Service
- Use reasonable rate limits
- Don't spam or harass users
- Be responsible with the data you collect

---

**Ready to extract LinkedIn data like a pro?** Star this repo and start scraping!
