import logging

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.utils.human_behavior import HumanBehavior
from linkedin_spider.utils.tracking import TrackingHandler

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for LinkedIn scrapers with minimal shared functionality."""

    def __init__(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        human_behavior: HumanBehavior,
        tracking_handler: TrackingHandler,
    ) -> None:
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.tracking_handler = tracking_handler

    def navigate_to_url(self, url: str) -> bool:
        """Navigate to URL and wait for page load."""
        try:
            self.driver.get(url)
            self.human_behavior.delay(2, 4)
            return self._wait_for_page_load()
        except Exception:
            return False

    def _wait_for_page_load(self, timeout: int = 10) -> bool:
        """Wait for page to fully load."""
        try:
            from selenium.webdriver.support.ui import WebDriverWait

            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except Exception:
            return False
        else:
            return True

    def log_action(self, action: str, details: str = "") -> None:
        """Log scraper action."""
        logger.info(f"[{self.__class__.__name__}] {action}: {details}")
