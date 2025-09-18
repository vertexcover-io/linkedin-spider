# LinkedIn Scraper - The Modern LinkedIn Data Extraction Tool

A powerful, reliable, and developer-friendly LinkedIn scraping library that actually works in 205. Extract profiles, companies, connections, and conversations with ease.

## Why Another LinkedIn Scraper?

Ever tried scraping LinkedIn and hit these roadblocks?

**Anti-Bot Mechanisms Gone Wild**

- LinkedIn's sophisticated detection systems block most scrapers within minutes
- Captchas appear faster than you can say "automation"
- IP bans that last longer than your patience

**Session Management Nightmares**

- Constant re-authentication breaking your workflows
- Sessions expiring at the worst possible moments
- Complex cookie management that makes your head spin

**Outdated Open Source Tools**

- Most libraries haven't been updated since LinkedIn changed their UI (again)
- Broken selectors and deprecated APIs everywhere
- Documentation that's more fiction than fact

**Performance & Reliability Issues**

- Inconsistent results that you can't depend on
- Memory leaks that crash your long-running scrapes
- No proper error handling or retry mechanisms

## How We Solve This

**Human-Like Behavior Simulation**

- Advanced anti-detection techniques that mimic real user interactions
- Randomized timing, mouse movements, and scroll patterns
- Smart delays and jitter to avoid pattern detection

**Intelligent Session Management**

- Persistent sessions that survive between requests
- Automatic session recovery and rotation
- Multiple authentication methods (cookies, credentials)

**Robust Error Handling**

- Automatic retry mechanisms with exponential backoff
- Graceful handling of rate limits and temporary blocks
- Comprehensive logging for debugging and monitoring

**Modern Architecture**

- Clean, typed Python code with comprehensive documentation
- Multiple interfaces: CLI, Python library, and MCP server
- Configurable and extensible for your specific needs

## Quick Start

### Installation

```bash
# Install with uv
pip install e .
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

### 3. MCP Server (Claude Integration)

### Environment Setup

Create a `.env` file:

```env
# Authentication (choose one method)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
# OR
LINKEDIN_COOKIE=your_li_at_cookie_value

# Configuration
HEADLESS=true
```

Use with Claude Code or other MCP-compatible tools:

```bash
# Start the MCP server
uv run linkedin_scraper_mcp

# Setup with claude code
claude mcp add <app-name> --transport sse <url>
```

### 4. Docker

Run in a containerized environment:

```bash
# Build the image
docker build -t linkedin-mcp .

# Run with environment variables
docker run -p <PORT> --env-file .env linkedin-mcp
```

### 5. Docker Compose

```bash
# Build and run the image
docker compose up --build
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

This tool is for educational and research purposes. Please:

- Respect LinkedIn's Terms of Service
- Use reasonable rate limits
- Don't spam or harass users
- Be responsible with the data you collect

---

**Ready to extract LinkedIn data like a pro?** Star this repo and start scraping!
