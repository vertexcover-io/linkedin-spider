"""LinkedIn MCP - A LinkedIn scraping tool with MCP integration."""

__version__ = "0.0.1"

# Import main components for easy access
from .core import LinkedInScraper, LinkedInAuth, ScraperConfig, DriverManager
from .scrapers import ProfileScraper, SearchScraper, SearchFilters
from .utils import HumanBehavior, CSPBypassHandler, LinkedInTrackingHandler

__all__ = [
    "LinkedInScraper",
    "LinkedInAuth",
    "ScraperConfig", 
    "DriverManager",
    "ProfileScraper",
    "SearchScraper",
    "SearchFilters",
    "HumanBehavior",
    "CSPBypassHandler",
    "LinkedInTrackingHandler"
]
