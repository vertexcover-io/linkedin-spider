"""LinkedIn Scraper - A modern LinkedIn scraping library."""

__version__ = "1.0.0"

from linkedin_scraper.core.auth import AuthManager
from linkedin_scraper.core.config import ScraperConfig
from linkedin_scraper.core.driver import DriverManager
from linkedin_scraper.core.scraper import LinkedInScraper

__all__ = [
    "LinkedInScraper",
    "AuthManager",
    "DriverManager",
    "ScraperConfig",
]
