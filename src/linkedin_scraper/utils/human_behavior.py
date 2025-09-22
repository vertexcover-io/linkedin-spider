import random
import time
from typing import Any

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from linkedin_scraper.core.config import ScraperConfig


class HumanBehavior:
    """Simulates human-like behavior for web automation."""

    def __init__(self, driver: Any, wait: Any, actions: Any, config: ScraperConfig) -> None:
        self.driver = driver
        self.wait = wait
        self.actions = actions
        self.config = config

    def delay(self, min_delay: float | None = None, max_delay: float | None = None) -> None:
        """Add human-like delay between actions."""
        try:
            if min_delay is None and max_delay is None:
                min_delay, max_delay = self.config.human_delay_range
            elif max_delay is None:
                if not isinstance(min_delay, (int, float)):
                    min_delay = 1.0
                max_delay = float(min_delay) + random.uniform(0.5, 2.0)

            min_delay = float(min_delay) if min_delay is not None else 1.0
            max_delay = float(max_delay) if max_delay is not None else 2.0

            if min_delay > max_delay:
                min_delay, max_delay = max_delay, min_delay

            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
        except (TypeError, ValueError):
            time.sleep(random.uniform(1.0, 2.0))

    def type_text(self, element: WebElement, text: str, clear_first: bool = True) -> None:
        """Type text with human-like behavior including occasional typos."""
        if clear_first:
            element.clear()
            self.delay(0.2, 0.5)

        if len(text) > 5 and random.random() < 0.1:
            self._type_with_typo(element, text)
        else:
            self._type_normally(element, text)

        if random.random() < 0.3:
            self.delay(0.3, 0.8)

    def click(self, element: WebElement) -> None:
        """Click element with human-like behavior."""
        try:
            if random.random() < 0.7:
                self._move_to_element_gradually(element)

            self.delay(0.1, 0.3)
            element.click()
            self.delay(0.2, 0.5)
        except Exception:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                self.delay(0.2, 0.5)
            except Exception:
                pass

    def scroll_to_element(self, element: WebElement) -> None:
        """Scroll to element with human-like behavior."""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element
            )
            self.delay(*self.config.scroll_pause_range)
        except Exception:
            pass

    def scroll_down(self, pixels: int = 300) -> None:
        """Scroll down by specified pixels."""
        self.driver.execute_script(f"window.scrollBy(0, {pixels});")
        self.delay(*self.config.scroll_pause_range)

    def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page."""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.delay(*self.config.scroll_pause_range)

    def random_mouse_movement(self) -> None:
        """Perform random mouse movements to appear more human."""
        try:
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")

            x = random.randint(100, viewport_width - 100)
            y = random.randint(100, viewport_height - 100)

            self.actions.move_by_offset(x, y).perform()
            self.delay(0.5, 1.5)
            self.actions.move_by_offset(-x, -y).perform()
        except Exception:
            pass

    def _type_with_typo(self, element: WebElement, text: str) -> None:
        """Type text with a realistic typo."""
        typo_pos = random.randint(1, len(text) - 1)
        typo_char = random.choice("qwertyuiopasdfghjklzxcvbnm")

        for char in text[:typo_pos]:
            element.send_keys(char)
            time.sleep(random.uniform(*self.config.typing_delay_range))

        element.send_keys(typo_char)
        time.sleep(random.uniform(0.1, 0.3))

        element.send_keys(Keys.BACKSPACE)
        time.sleep(random.uniform(0.1, 0.2))

        for char in text[typo_pos:]:
            element.send_keys(char)
            time.sleep(random.uniform(*self.config.typing_delay_range))

    def _type_normally(self, element: WebElement, text: str) -> None:
        """Type text normally with realistic delays."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*self.config.typing_delay_range))

    def _move_to_element_gradually(self, element: WebElement) -> None:
        """Move mouse to element with realistic path."""
        try:
            element_rect = element.rect
            element_x = element_rect["x"] + element_rect["width"] // 2
            element_y = element_rect["y"] + element_rect["height"] // 2

            variance = self.config.mouse_move_variance
            target_x = element_x + random.randint(-variance, variance)
            target_y = element_y + random.randint(-variance, variance)

            self.actions.move_to_element_with_offset(
                element, target_x - element_x, target_y - element_y
            ).perform()
            self.delay(0.1, 0.3)
        except Exception:
            try:
                self.actions.move_to_element(element).perform()
                self.delay(0.1, 0.3)
            except Exception:
                pass
