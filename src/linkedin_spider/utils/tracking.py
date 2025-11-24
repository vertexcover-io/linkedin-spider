import contextlib
import random
import time
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TrackingHandler:
    """Handles anti-tracking and detection avoidance."""

    def __init__(self, driver: Any, wait: Any, actions: Any) -> None:
        self.driver = driver
        self.wait = wait
        self.actions = actions

    def inject_anti_detection_scripts(self) -> None:
        """Inject scripts to avoid detection."""
        scripts = [
            self._get_webdriver_removal_script(),
            self._get_navigator_override_script(),
            self._get_permissions_override_script(),
        ]

        for script in scripts:
            with contextlib.suppress(Exception):
                self.driver.execute_script(script)

    def simulate_natural_browsing(self) -> None:
        """Simulate natural browsing behavior."""
        if random.random() < 0.7:
            self._random_scroll()

        if random.random() < 0.3:
            self._random_mouse_movement()

        if random.random() < 0.2:
            self._simulate_reading_pause()

    def wait_for_element_naturally(self, element: WebElement, min_duration: float = 0.3) -> bool:
        """Wait for element with natural interaction simulation."""
        try:
            short_wait = WebDriverWait(self.driver, 2)
            short_wait.until(EC.visibility_of(element))

            if self._simulate_element_interaction(element):
                time.sleep(max(min_duration, 0.1))
                return True

            return False
        except TimeoutException:
            return False

    def _random_scroll(self) -> None:
        """Perform random scrolling."""
        try:
            scroll_distance = random.randint(100, 400)
            can_scroll = self.driver.execute_script("""
                return (window.pageYOffset || document.documentElement.scrollTop) <
                       (document.documentElement.scrollHeight - document.documentElement.clientHeight);
            """)

            if can_scroll:
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(random.uniform(0.5, 1.5))
        except Exception:
            pass

    def _random_mouse_movement(self) -> None:
        """Perform random mouse movements."""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, .clickable")
            if elements:
                random_element = random.choice(elements[:10])
                self.actions.move_to_element(random_element).perform()
                time.sleep(random.uniform(0.2, 0.8))
        except Exception:
            pass

    def _simulate_reading_pause(self) -> None:
        """Simulate reading pause."""
        time.sleep(random.uniform(1.0, 3.0))

    def _simulate_element_interaction(self, element: WebElement) -> bool:
        """Simulate natural interaction with element."""
        try:
            self.actions.move_to_element(element).perform()
            time.sleep(random.uniform(0.1, 0.3))
            return True
        except Exception:
            return False

    def _get_webdriver_removal_script(self) -> str:
        """Script to remove webdriver property."""
        return """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        """

    def _get_navigator_override_script(self) -> str:
        """Script to override navigator properties."""
        return """
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: {}},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }
            ],
            configurable: true
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
            configurable: true
        });
        """

    def handle_search_result_tracking(self, containers: list[WebElement]) -> list[WebElement]:
        processed_containers = []

        for container in containers:
            try:
                self.wait_for_element_naturally(container, 0.2)

                try:
                    if (
                        container.get_attribute("data-view-name")
                        == "search-entity-result-universal-template"
                    ):
                        container.click()
                        time.sleep(0.05)
                        self.driver.execute_script("window.history.back();")
                        time.sleep(0.05)
                except:
                    pass

                processed_containers.append(container)

            except Exception:
                continue

        return processed_containers

    def _get_permissions_override_script(self) -> str:
        """Script to override permissions API."""
        return """
        const originalQuery = window.navigator.permissions.query;
        if (originalQuery) {
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        }
        """
