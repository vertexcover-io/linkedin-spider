import time
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BrowserUtils:
    """Utility functions for browser operations."""

    def __init__(self, driver: Any, wait: Any) -> None:
        self.driver = driver
        self.wait = wait

    def wait_for_page_load(self, timeout: int = 10) -> bool:
        """Wait for page to fully load."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            return False

    def safe_find_element(self, by: By, value: str, timeout: int = 5) -> WebElement | None:
        """Safely find element with timeout."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None

    def safe_find_elements(self, by: By, value: str, timeout: int = 5) -> list[WebElement]:
        """Safely find elements with timeout."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            return self.driver.find_elements(by, value)
        except TimeoutException:
            return []

    def get_element_text_safe(self, element: WebElement) -> str:
        """Safely get element text."""
        try:
            return element.text.strip()
        except Exception:
            return ""

    def get_element_attribute_safe(self, element: WebElement, attribute: str) -> str:
        """Safely get element attribute."""
        try:
            value = element.get_attribute(attribute)
            return value.strip() if value else ""
        except Exception:
            return ""

    def click_element_safe(self, element: WebElement) -> bool:
        """Safely click element."""
        try:
            element.click()
            return True
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def refresh_and_wait(self, timeout: int = 10) -> None:
        """Refresh page and wait for load."""
        self.driver.refresh()
        self.wait_for_page_load(timeout)

    def navigate_back(self) -> None:
        """Navigate back in browser history."""
        try:
            self.driver.back()
            time.sleep(1)
        except Exception:
            pass

    def execute_script_safe(self, script: str) -> Any | None:
        """Safely execute JavaScript."""
        try:
            return self.driver.execute_script(script)
        except Exception:
            return None
