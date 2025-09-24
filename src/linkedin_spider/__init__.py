"""LinkedIn Scraper - A modern LinkedIn scraping library."""

__version__ = "1.0.0"

from linkedin_spider.core.auth import AuthManager
from linkedin_spider.core.config import ScraperConfig
from linkedin_spider.core.driver import DriverManager
from linkedin_spider.core.scraper import LinkedinSpider

__all__ = [
    "LinkedinSpider",
    "AuthManager",
    "DriverManager",
    "ScraperConfig",
]
