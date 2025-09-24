# linkedin-spider-mcp

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
# Clone the repo
github.com/vertexcover-io/linkedin-mcp-py
cd linkedin-mcp-py
# Install with uv
uv sync
```

> [!NOTE]
> **Authentication Update:** LinkedIn has enhanced their anti-bot mechanisms, temporarily affecting cookie-based authentication. We recommend using the email/password authentication method for reliable access. We are actively working on restoring full cookie authentication support.

## Different ways to use it

### 1. Python Library

Perfect for integration into your existing Python applications:

```python
from linkedin_scraper import LinkedInSpider, ScraperConfig

config = ScraperConfig(headless=True, page_load_timeout=30)
```

```python
# Authenticate (use either email/password or cookie).
# Authentication is mostly done once and the session is saved in the chrome profile
scraper = LinkedInSpider(
    email="your_email@example.com",
    password="your_password",
    config=config
)
```

```python
# Search for profiles
results = scraper.search_profiles("software engineer", max_results=10)
```

**Output sample:**
```json
[
  {
    "name": "John Doe",
    "title": "Senior Software Engineer at Google",
    "location": "San Francisco, CA",
    "profile_url": "https://linkedin.com/in/johndoe",
    "connections": "500+"
  },
  {
    "name": "Jane Smith",
    "title": "Software Engineer at Microsoft",
    "location": "Seattle, WA",
    "profile_url": "https://linkedin.com/in/janesmith",
    "connections": "200+"
  }
]
```

```python
# Scrape individual profile
profile = scraper.scrape_profile("https://linkedin.com/in/someone")
```

**Output sample:**
```json
{
  "name": "John Doe",
  "title": "Senior Software Engineer",
  "location": "San Francisco, CA",
  "about": "Passionate software engineer with 8+ years of experience...",
  "experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Google",
      "duration": "2021 - Present",
      "description": "Leading backend development for search infrastructure..."
    }
  ],
  "education": [
    {
      "school": "Stanford University",
      "degree": "BS Computer Science",
      "years": "2013 - 2017"
    }
  ],
  "skills": ["Python", "Java", "Kubernetes", "AWS"]
}
```

```python
# Scrape company information
company = scraper.scrape_company("https://linkedin.com/company/tech-corp")
```

**Output sample:**
```json
{
  "name": "TechCorp Inc",
  "industry": "Software Development",
  "company_size": "1,001-5,000 employees",
  "headquarters": "San Francisco, CA",
  "founded": "2010",
  "specialties": ["Cloud Computing", "AI/ML", "Data Analytics"],
  "description": "Leading technology company focused on enterprise solutions...",
  "website": "https://techcorp.com",
  "follower_count": "45,230"
}
```

```python
# Don't forget to clean up
scraper.close()
```

For more examples : [examples](./examples)

### 2. Command Line Interface

Great for quick data extraction and scripting:

```bash
uv run linkedin-spider-cli search -q "product manager" -n 10 -o results.json
uv run linkedin-spider-cli profile -u "https://linkedin.com/in/johndoe" -o profile.json
uv run linkedin-spider-cli company -u "https://linkedin.com/company/openai" -o company.json
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

# Transport (optional, defaults to stdio)
TRANSPORT=sse
HOST=127.0.0.1
PORT=8000
```

Start the MCP server:

```bash
# Show available transport options
uv run linkedin_mcp

# Start with specific transport
uv run linkedin_mcp sse
uv run linkedin_mcp http --host 0.0.0.0 --port 9000
uv run linkedin_mcp stdio

# Or use environment variables
TRANSPORT=sse uv run linkedin_mcp
```

#### Claude Code Integration

```bash
# Add to Claude Code
claude mcp add linkedin-spider --transport sse <server-url> 
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
    "linkedin-spider": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "LINKEDIN_EMAIL=your_email@example.com",
        "-e", "LINKEDIN_PASSWORD=your_password",
        "-e", "HEADLESS=true",
        "-e", "TRANSPORT=stdio",
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
    "linkedin-spider": {
      "command": "linkedin-mcp",
      "args": ["stdio"],
      "env": {
        "LINKEDIN_EMAIL": "your_email@example.com",
        "LINKEDIN_PASSWORD": "your_password",
        "HEADLESS": "true"
      }
    }
  }
}
```



## Docker Development & Testing

For development and testing with Docker, you can use a single image with different transport configurations:

### Build the Docker Image

```bash
# Build once for all transport types
docker build -t linkedin-mcp .
```

### Run with Different Transports

#### SSE Server
```bash
docker run -p 8000:8000 -e TRANSPORT=sse --env-file .env linkedin-mcp
```

#### HTTP Server
```bash
docker run -p 8000:8000 -e TRANSPORT=http --env-file .env linkedin-mcp
```

#### STDIO Server
```bash
docker run --rm -i -e TRANSPORT=stdio --env-file .env linkedin-mcp
```


## Authentication Methods

### Method 1: LinkedIn Cookie

1. Login to LinkedIn in your browser
2. Open Developer Tools (F12)
3. Go to Application/Storage → Cookies → linkedin.com
4. Copy the `li_at` cookie value
5. Use it in your code:

```python
scraper = LinkedInSpider(li_at_cookie="your_cookie_value")
```

### Method 2: Email & Password (Recommended)

```python
scraper = LinkedInSpider(
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
