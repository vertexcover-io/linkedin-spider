import logging
import re
from typing import Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ConnectionScraper(BaseScraper):
    """Scraper for LinkedIn connections and connection requests."""

    def _find_element_in_parent(self, parent: WebElement, by: By, value: str) -> WebElement | None:
        """Find element within parent element."""
        try:
            return parent.find_element(by, value)
        except Exception:
            return None

    def _is_valid_linkedin_url(self, url: str) -> bool:
        if not url or not isinstance(url, str) or url == "N/A":
            return False
        linkedin_pattern = r"^https?://(www\.)?linkedin\.com/in/"
        return bool(re.match(linkedin_pattern, url))

    def scrape_incoming_connections(self, max_results: int = 10) -> list[dict[str, Any]]:
        """Scrape incoming connection requests."""
        self.log_action("INFO", f"Scraping incoming connection requests (max: {max_results})")
        incoming_url = "https://www.linkedin.com/mynetwork/invitation-manager/received/"
        self.driver.get(incoming_url)
        self.human_behavior.delay(1, 3)

        connections = []

        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='listitem'][componentkey]")
                )
            )

            while len(connections) < max_results:
                containers = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listitem'][componentkey]"
                )

                for container in containers:
                    if len(connections) >= max_results:
                        break

                    data = self._extract_incoming_connection_data(container)
                    if data and data not in connections:
                        connections.append(data)

                if not self._handle_load_more() or len(connections) >= max_results:
                    break

            self.log_action("SUCCESS", f"Extracted {len(connections)} incoming connections")
        except Exception as e:
            self.log_action("ERROR", f"Error scraping incoming connections: {e!s}")
            return []
        else:
            return connections

    def scrape_outgoing_connections(self, max_results: int = 10) -> list[dict[str, Any]]:
        """Scrape outgoing connection requests."""
        self.log_action("INFO", f"Scraping outgoing connection requests (max: {max_results})")
        outgoing_url = "https://www.linkedin.com/mynetwork/invitation-manager/sent/"
        self.driver.get(outgoing_url)
        self.human_behavior.delay(1, 3)

        connections = []

        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='listitem'][componentkey]")
                )
            )

            while len(connections) < max_results:
                containers = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[role='listitem'][componentkey]"
                )

                for container in containers:
                    if len(connections) >= max_results:
                        break

                    data = self._extract_outgoing_connection_data(container)
                    if data and data not in connections:
                        connections.append(data)

                if not self._handle_load_more() or len(connections) >= max_results:
                    break

            self.log_action("SUCCESS", f"Extracted {len(connections)} outgoing connections")
        except Exception as e:
            self.log_action("ERROR", f"Error scraping outgoing connections: {e!s}")
            return []
        else:
            return connections

    def send_connection_request(self, profile_url: str, note: str | None = None) -> bool:
        """Send a connection request to a profile."""
        if not self._is_valid_linkedin_url(profile_url):
            self.log_action("ERROR", f"Invalid profile URL: {profile_url}")
            return False

        self.log_action("INFO", f"Sending connection request to: {profile_url}")

        try:
            self.driver.get(profile_url)

            if not self._wait_for_page_load():
                self.log_action("ERROR", "Failed to load profile page")
                return False

            self.human_behavior.delay(1, 2)

            # Try to find a /preload/custom-invite/ link and navigate directly
            # Clicking the <a> link via SPA routing often fails to open the modal,
            # but navigating directly to the invite URL works reliably.
            if self._navigate_to_invite_url():
                if not self._wait_for_modal():
                    self.log_action("ERROR", "Connection modal not found after direct navigation")
                    return False
            else:
                # Fallback: click Connect button on the page
                if not self._click_connect_button():
                    self.log_action("ERROR", "Connect button not found")
                    return False

                if not self._wait_for_modal():
                    self.log_action("ERROR", "Connection modal not found")
                    return False

            if note and note.strip():
                return self._send_with_note(note)
            else:
                return self._send_without_note()

        except Exception as e:
            self.log_action("ERROR", f"Connection request failed: {e!s}")
            return False

    def _navigate_to_invite_url(self) -> bool:
        """Find the invite URL from the profile page and navigate to it directly."""
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/preload/custom-invite/']"
            )
            for element in elements:
                href = element.get_attribute("href")
                if href:
                    self.log_action("INFO", f"Navigating to invite URL: {href}")
                    self.human_behavior.delay(0.5, 1.0)
                    self.driver.get(href)
                    self.human_behavior.delay(1, 2)
                    return True
        except (NoSuchElementException, Exception):
            logger.debug("No custom-invite link found on profile page")
        return False

    def _wait_for_page_load(self) -> bool:
        try:
            self.wait.until(lambda driver: driver.current_url != "about:blank")
        except TimeoutException:
            return False
        else:
            return "linkedin.com/in/" in self.driver.current_url

    def _get_profile_name(self) -> str:
        """Extract the profile owner's name from the page."""
        # Try h1 first (classic layout)
        try:
            heading = self.driver.find_element(By.CSS_SELECTOR, "h1")
            name = heading.text.strip()
            if name:
                return name
        except NoSuchElementException:
            pass
        # Fallback: extract from page title ("Pawan Y | LinkedIn")
        try:
            title = self.driver.title or ""
            if "|" in title:
                return title.split("|")[0].strip()
        except (NoSuchElementException, TimeoutException):
            pass
        return ""

    def _is_target_connect_button(self, element: WebElement, profile_name: str) -> bool:
        """Check if a connect button is for the target profile, not a sidebar suggestion."""
        aria = element.get_attribute("aria-label") or ""
        if not aria:
            return True  # no aria-label — can't distinguish, allow it
        # aria-label like "Invite Pawan Y to connect" — check it matches the target name
        if profile_name:
            name_lower = profile_name.lower()
            aria_lower = aria.lower()
            # Try full name first, fall back to first name for truncated aria-labels
            if name_lower in aria_lower:
                return True
            first_name = profile_name.split()[0].lower()
            return first_name in aria_lower
        return True

    def _click_connect_button(self) -> bool:
        profile_name = self._get_profile_name()

        # LinkedIn renders the Connect action as either <a> or <button> depending on layout
        # Note: a[href*='/preload/custom-invite/'] is intentionally excluded here —
        # it's handled by _navigate_to_invite_url() via driver.get() which is more
        # reliable than clicking the SPA link.
        css_selectors = [
            "a[aria-label*='Invite'][aria-label*='connect']",
            "button[aria-label*='Invite'][aria-label*='connect']",
            "button[data-control-name='connect']",
        ]

        # Wait for at least one connect element to be present before attempting clicks
        combined_css = ", ".join(css_selectors)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, combined_css))
            )
        except TimeoutException:
            logger.debug("No connect button appeared within timeout, trying dropdown")

        for selector in css_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if (
                        element.is_displayed()
                        and element.is_enabled()
                        and self._is_target_connect_button(element, profile_name)
                    ):
                        self.log_action("INFO", f"Clicking connect button: {selector}")
                        self.human_behavior.delay(0.5, 1.0)
                        element.click()
                        return True
            except (NoSuchElementException, Exception):
                logger.debug("Failed to find connect button with selector: %s", selector)
                continue

        # XPath fallback — match by visible text content
        xpath_selectors = [
            "//a[normalize-space(.)='Connect']",
            "//button[normalize-space(.)='Connect']",
        ]

        for xpath in xpath_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if (
                        element.is_displayed()
                        and element.is_enabled()
                        and self._is_target_connect_button(element, profile_name)
                    ):
                        self.log_action("INFO", f"Clicking connect button: {xpath}")
                        self.human_behavior.delay(0.5, 1.0)
                        element.click()
                        return True
            except (NoSuchElementException, Exception):
                logger.debug("Failed to find connect button with xpath: %s", xpath)
                continue

        return self._try_dropdown_connect()

    def _try_dropdown_connect(self) -> bool:
        dropdown_selectors = [
            "button[aria-label='More']",
            "button[aria-label*='More actions']",
            "button.artdeco-dropdown__trigger[aria-label*='More actions']",
            "button[data-view-name='profile-overflow-button']",
        ]

        for selector in dropdown_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for dropdown in elements:
                    if dropdown.is_displayed() and dropdown.is_enabled():
                        self.log_action("INFO", f"Opening dropdown: {selector}")
                        self.human_behavior.delay(0.5, 1.0)
                        try:
                            dropdown.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", dropdown)

                        self.human_behavior.delay(2.0, 3.0)

                        if self._click_dropdown_connect():
                            return True

            except (NoSuchElementException, Exception):
                logger.debug("Failed to find dropdown with selector: %s", selector)
                continue

        return False

    def _click_dropdown_connect(self) -> bool:
        wait_selectors = (
            "div[data-view-name='edge-creation-connect-action'],"
            " a[href*='custom-invite'],"
            " div[aria-label*='Invite'][aria-label*='connect']"
        )
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selectors))
            )
        except TimeoutException:
            return False

        # First, try to extract the custom-invite URL and navigate directly.
        # Clicking the <a> via SPA routing often fails to open the modal,
        # but driver.get() to the invite URL works reliably.
        invite_url_selectors = [
            "a[href*='/preload/custom-invite/']",
            "a[href*='custom-invite']",
        ]
        for selector in invite_url_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        href = element.get_attribute("href")
                        if href:
                            self.log_action(
                                "INFO", f"Navigating to invite URL from dropdown: {href}"
                            )
                            self.human_behavior.delay(0.5, 1)
                            self.driver.get(href)
                            self.human_behavior.delay(1, 2)
                            return True
            except (NoSuchElementException, Exception):
                logger.debug("Failed to find invite URL with selector: %s", selector)
                continue

        # Fallback: click non-link connect items in the dropdown
        click_selectors = [
            "div[aria-label*='Invite'][aria-label*='connect']",
            "div.artdeco-dropdown div[aria-label^='Invite'][aria-label$='connect']",
            ".artdeco-dropdown__item[aria-label*='connect']",
            "a[aria-label*='Invite'][aria-label*='connect']",
        ]

        for selector in click_selectors:
            try:
                connect_items = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for connect_item in connect_items:
                    if connect_item.is_displayed():
                        self.log_action("INFO", f"Clicking dropdown connect: {selector}")
                        self.human_behavior.delay(0.5, 1)

                        try:
                            connect_item.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", connect_item)

                        self.human_behavior.delay(1, 2)
                        return True

            except (NoSuchElementException, Exception):
                logger.debug("Failed to click dropdown connect with selector: %s", selector)
                continue

        return False

    def _wait_for_modal(self) -> bool:
        modal_selectors = [
            "div.artdeco-modal.artdeco-modal--layer-default[role='dialog']",
            "div.artdeco-modal-overlay.artdeco-modal-overlay--layer-default",
            "div[aria-labelledby*='send-invite']",
            "div[data-view-name='invite-connect-modal']",
            "div.send-invite.artdeco-modal",
        ]

        try:
            modal = WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    *(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, s))
                        for s in modal_selectors
                    )
                )
            )
        except TimeoutException:
            return False
        else:
            return modal is not False

    def _send_with_note(self, note: str) -> bool:
        short_wait = WebDriverWait(self.driver, 10)
        try:
            add_note_selectors = [
                "button[aria-label*='Add a note']",
                "button[aria-label*='Add a free note']",
                "div.artdeco-modal button[data-control-name='add_note']",
                "div.send-invite button.artdeco-button--muted",
            ]

            try:
                add_note_button = short_wait.until(
                    EC.any_of(
                        *(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, s))
                            for s in add_note_selectors
                        )
                    )
                )
            except TimeoutException:
                return False

            add_note_button.click()

            textarea_selectors = [
                "div.artdeco-modal textarea[name='message']",
                "div.send-invite textarea",
                "textarea[placeholder*='Add a note']",
                "div.artdeco-modal textarea",
            ]

            try:
                textarea = short_wait.until(
                    EC.any_of(
                        *(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, s))
                            for s in textarea_selectors
                        )
                    )
                )
            except TimeoutException:
                return False

            textarea.clear()
            self.human_behavior.type_text(textarea, note)

            send_button_selectors = [
                "button[aria-label*='Send invitation']",
                "div.artdeco-modal button[data-control-name='send']",
                "div.send-invite button.artdeco-button--primary",
                "button.artdeco-button--primary[type='submit']",
            ]

            try:
                send_button = short_wait.until(
                    EC.any_of(
                        *(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, s))
                            for s in send_button_selectors
                        )
                    )
                )
            except TimeoutException:
                return False

            send_button.click()

            self.log_action("SUCCESS", "Connection request sent with note")
        except Exception as e:
            self.log_action("ERROR", f"Failed to send with note: {e!s}")
            return False
        else:
            return True

    def _send_without_note(self) -> bool:
        try:
            send_button_selectors = [
                "button[aria-label*='Send without a note']",
                "button[aria-label*='Send now']",
                "div.artdeco-modal button[data-control-name='send_without_note']",
                "div.send-invite button.artdeco-button--primary:not([aria-label*='Add'])",
                "button.artdeco-button--primary[type='submit']",
            ]

            try:
                send_button = WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        *(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, s))
                            for s in send_button_selectors
                        )
                    )
                )
            except TimeoutException:
                return False

            send_button.click()

            self.log_action("SUCCESS", "Connection request sent without note")
        except Exception as e:
            self.log_action("ERROR", f"Failed to send without note: {e!s}")
            return False
        else:
            return True

    def _extract_incoming_connection_data(self, container: WebElement) -> dict[str, str] | None:
        data = {}

        try:
            name_link = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']:not([tabindex])")
            data["name"] = name_link.text.strip() or "N/A"
            data["profile_url"] = name_link.get_attribute("href") or "N/A"
        except Exception:
            data["name"] = "N/A"
            data["profile_url"] = "N/A"

        paragraphs = container.find_elements(By.CSS_SELECTOR, "p")

        headline_text = "N/A"
        try:
            for p in paragraphs:
                txt = p.text.strip()
                if txt and not any(
                    word in txt.lower()
                    for word in [
                        "sent",
                        "ago",
                        "yesterday",
                        "week",
                        "month",
                        "hour",
                        "minute",
                        "mutual connection",
                    ]
                ):
                    headline_text = txt
                    break
        except Exception:
            logger.debug("Failed to extract incoming connection headline")
        data["headline"] = headline_text

        time_text = "N/A"
        try:
            for p in paragraphs:
                txt = p.text.strip().lower()
                if any(
                    word in txt
                    for word in ["sent", "ago", "yesterday", "week", "month", "hour", "minute"]
                ):
                    time_text = p.text.strip()
                    break
        except Exception:
            logger.debug("Failed to extract incoming connection time")
        data["time_sent"] = time_text

        mutual_connections_text = "N/A"
        try:
            for p in paragraphs:
                txt = p.text.strip()
                if "mutual connection" in txt.lower():
                    mutual_connections_text = txt
                    break
        except Exception:
            logger.debug("Failed to extract incoming mutual connections")
        data["mutual_connections"] = mutual_connections_text

        try:
            span_element = container.find_element(
                By.CSS_SELECTOR, "span[data-testid='expandable-text-box']"
            )
            message_text = self.driver.execute_script(
                """
                var element = arguments[0];
                var text = '';
                for (var i = 0; i < element.childNodes.length; i++) {
                    if (element.childNodes[i].nodeType === Node.TEXT_NODE) {
                        text += element.childNodes[i].textContent;
                    }
                }
                return text.trim();
            """,
                span_element,
            )
            data["message"] = message_text or "N/A"
        except Exception:
            data["message"] = "N/A"

        try:
            img_element = container.find_element(By.CSS_SELECTOR, "img[alt*='profile picture']")
            data["image_url"] = img_element.get_attribute("src") or "N/A"
        except Exception:
            data["image_url"] = "N/A"

        return data if data.get("name") != "N/A" else None

    def _extract_outgoing_connection_data(self, container: WebElement) -> dict[str, str] | None:
        data = {}

        try:
            name_link = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']:not([tabindex])")
            data["name"] = name_link.text.strip() or "N/A"
            data["profile_url"] = name_link.get_attribute("href") or "N/A"
        except Exception:
            data["name"] = "N/A"
            data["profile_url"] = "N/A"

        try:
            headline_candidates = container.find_elements(By.CSS_SELECTOR, "p")
            headline_text = "N/A"
            for p in headline_candidates:
                txt = p.text.strip()
                if txt and not any(
                    word in txt.lower()
                    for word in ["sent", "ago", "yesterday", "week", "month", "hour", "minute"]
                ):
                    headline_text = txt
                    break
            data["headline"] = headline_text
        except Exception:
            data["headline"] = "N/A"

        try:
            time_candidates = container.find_elements(By.CSS_SELECTOR, "p")
            time_text = "N/A"
            for p in time_candidates:
                txt = p.text.strip().lower()
                if any(
                    word in txt
                    for word in ["sent", "ago", "yesterday", "week", "month", "hour", "minute"]
                ):
                    time_text = p.text.strip()
                    break
            data["time_sent"] = time_text
        except Exception:
            data["time_sent"] = "N/A"

        try:
            span_element = container.find_element(
                By.CSS_SELECTOR, "span[data-testid='expandable-text-box']"
            )
            message_text = self.driver.execute_script(
                """
                var element = arguments[0];
                var text = '';
                for (var i = 0; i < element.childNodes.length; i++) {
                    if (element.childNodes[i].nodeType === Node.TEXT_NODE) {
                        text += element.childNodes[i].textContent;
                    }
                }
                return text.trim();
            """,
                span_element,
            )
            data["message"] = message_text or "N/A"
        except Exception:
            data["message"] = "N/A"

        try:
            img_element = container.find_element(By.CSS_SELECTOR, "img[alt*='profile picture']")
            data["image_url"] = img_element.get_attribute("src") or "N/A"
        except Exception:
            data["image_url"] = "N/A"

        return data if data.get("name") != "N/A" else None

    def _handle_load_more(self) -> bool:
        try:
            load_more_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button:contains('Load more')"
            )
            if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                self.human_behavior.delay(0.5, 1.5)
                load_more_btn.click()
                self.human_behavior.delay(2, 4)
                return True
        except Exception:
            try:
                load_more_btn = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Load more')]"
                )
                if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                    self.human_behavior.delay(0.5, 1.5)
                    load_more_btn.click()
                    self.human_behavior.delay(2, 4)
                    return True
            except Exception:
                logger.debug("Failed to find load more button")
        return False

    def scrape(self, *args, **kwargs) -> Any:
        """Main scraping implementation."""
        return self._scrape_connections(*args, **kwargs)

    def _scrape_connections(
        self, url: str, max_results: int, connection_type: str
    ) -> list[dict[str, Any]]:
        """Legacy method for backward compatibility."""
        if connection_type == "incoming":
            return self.scrape_incoming_connections(max_results)
        elif connection_type == "outgoing":
            return self.scrape_outgoing_connections(max_results)
        else:
            return []
