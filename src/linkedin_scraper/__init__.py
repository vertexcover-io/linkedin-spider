"""LinkedIn Scraper - A modern LinkedIn scraping library."""

__version__ = "1.0.0"

from .core.auth import AuthManager
from .core.config import ScraperConfig
from .core.driver import DriverManager
from .core.scraper import LinkedInScraper

__all__ = [
    "LinkedInScraper",
    "AuthManager",
    "DriverManager",
    "ScraperConfig",
]
