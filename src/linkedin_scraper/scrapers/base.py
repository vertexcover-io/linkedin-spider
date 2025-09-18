from abc import ABC

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from ..utils.human_behavior import HumanBehavior
from ..utils.tracking import TrackingHandler


class BaseScraper(ABC):
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
            return True
        except Exception:
            return False

    def log_action(self, action: str, details: str = "") -> None:
        """Log scraper action."""
        print(f"[{self.__class__.__name__}] {action}: {details}")
