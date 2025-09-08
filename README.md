# LinkedIn MCP Server

A high-performance LinkedIn scraper built as a Model Context Protocol (MCP) server with advanced anti-detection capabilities and human-like behavior simulation.

## Features

- **Profile Scraping**: Extract comprehensive LinkedIn profile data including experience, education, skills, and contact information
- **Advanced Search**: Search profiles with location and industry filters, automatic pagination support
- **Connection Management**: Scrape incoming and outgoing connection requests with message content
- **Anti-Detection**: Built-in stealth mode, human behavior simulation, and tracking protection
- **MCP Integration**: Seamless integration with Claude and other MCP-compatible clients
- **Session Management**: Persistent browser sessions with automatic recovery
- **Robust Error Handling**: Comprehensive exception handling and retry mechanisms

## Prerequisites

- Python 3.10 or higher
- Chrome browser (latest version recommended)
- LinkedIn account with valid session cookie

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amankumarsingh77/linkedin-mcp.git
cd linkedin-mcp
```

2. Install using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

3. Install ChromeDriver:
   - Download from [ChromeDriver](https://chromedriver.chromium.org/)
   - Add to your PATH or place in project directory

## Configuration

### MCP Configuration

Add to your MCP configuration file (e.g., `.mcp.json`):

```json
{
  "mcpServers": {
    "linkedin-scraper": {
      "command": "uv",
      "args": ["run", "linkedin_mcp"],
      "cwd": "/path/to/linkedin-scraper",
      "env": {
        "cookie": "YOUR_LINKEDIN_LI_AT_COOKIE"
      }
    }
  }
}
```

### Environment Setup

Create a `.env` file in the project root:

```env
LI_AT_COOKIE=your_linkedin_li_at_cookie_here
HEADLESS=true
STEALTH_MODE=true
```

### Obtaining LinkedIn Cookie

1. Log in to LinkedIn in your browser
2. Open Developer Tools (F12)
3. Go to Application > Cookies > https://linkedin.com
4. Copy the value of the `li_at` cookie
5. Add it to your configuration

## Usage

### MCP Server

The server provides the following tools:

#### `scrape_profile`
```json
{
  "profile_url": "https://www.linkedin.com/in/username"
}
```

#### `search_profiles`
```json
{
  "query": "Software Engineer",
  "max_results": 10,
  "location": "San Francisco",
  "industry": "Technology"
}
```

#### `scrape_incoming_connections`
```json
{
  "max_results": 20
}
```

#### `scrape_outgoing_connections`
```json
{
  "max_results": 15
}
```

#### `get_session_status`
```json
{}
```

#### `reset_session`
```json
{}
```

### Direct Usage

```python
from linkedin_mcp.core.linkedin_scraper import LinkedInScraper

scraper = LinkedInScraper(li_at_cookie="your_cookie_here")

# Scrape a profile
profile = scraper.scrape_profile("https://www.linkedin.com/in/username")

# Search profiles
results = scraper.search_profiles("Software Engineer", max_results=10)

# Get connections
incoming = scraper.scrape_incoming_connections(max_results=20)
outgoing = scraper.scrape_outgoing_connections(max_results=15)
```

## Response Format

### Profile Data
```json
{
  "name": "John Doe",
  "headline": "Software Engineer at Tech Company",
  "location": "San Francisco, CA",
  "profile_url": "https://www.linkedin.com/in/johndoe",
  "about": "Experienced software engineer...",
  "experience": [...],
  "education": [...],
  "skills": [...],
  "contact_info": {...}
}
```

### Search Results
```json
[
  {
    "name": "Jane Smith",
    "headline": "Senior Developer",
    "location": "New York, NY",
    "profile_url": "https://www.linkedin.com/in/janesmith",
    "image_url": "https://..."
  }
]
```

### Connection Data
```json
[
  {
    "name": "Alice Johnson",
    "profile_url": "https://www.linkedin.com/in/alicejohnson",
    "headline": "Product Manager",
    "time_sent": "2 weeks ago",
    "message": "Hi Alice, I'd love to connect...",
    "mutual_connections": "5 mutual connections",
    "image_url": "https://..."
  }
]
```

## Architecture

```
linkedin_mcp/
├── core/                    # Core functionality
│   ├── linkedin_scraper.py  # Main scraper class
│   ├── session_manager.py   # Session management
│   ├── driver_manager.py    # WebDriver setup
│   └── authentication.py    # LinkedIn authentication
├── scrapers/                # Specialized scrapers
│   ├── profile_scraper.py   # Profile data extraction
│   ├── search_scraper.py    # Search functionality
│   └── connection_scraper.py # Connection management
├── utils/                   # Utility modules
│   ├── human_behavior.py    # Behavior simulation
│   └── tracking_handler.py  # Anti-detection
└── server.py               # MCP server implementation
```

## Anti-Detection Features

- **Stealth Mode**: Bypasses common bot detection mechanisms
- **Human Behavior**: Randomized delays, mouse movements, and scrolling patterns
- **User Agent Rotation**: Dynamic user agent switching
- **Request Throttling**: Intelligent rate limiting
- **Session Persistence**: Maintains logged-in state across requests

## Rate Limits

- Profile scraping: 1-2 profiles per minute
- Search operations: 10-20 results per minute
- Connection requests: 5-10 per minute

## Error Handling

The scraper includes comprehensive error handling for:

- Network timeouts and connection issues
- LinkedIn rate limiting and blocking
- Element not found exceptions
- Session expiration and re-authentication
- Browser crashes and recovery

## Troubleshooting

### Common Issues

**Session expired**: Update your `li_at` cookie value

**ChromeDriver not found**: Ensure ChromeDriver is installed and in PATH

**Rate limited**: Reduce request frequency and enable stealth mode

**Elements not found**: LinkedIn may have updated their UI - check for updates

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and research purposes only. Users are responsible for complying with LinkedIn's Terms of Service and applicable laws. The authors are not responsible for any misuse or violations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation and troubleshooting guides