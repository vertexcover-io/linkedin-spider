import contextlib
import re
from typing import Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.scrapers.base import BaseScraper


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
            return connections

        except Exception as e:
            self.log_action("ERROR", f"Error scraping incoming connections: {e!s}")
            return []

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
            return connections

        except Exception as e:
            self.log_action("ERROR", f"Error scraping outgoing connections: {e!s}")
            return []

    def scrape_connections(
        self, connection_type: str = "both", max_results: int = 10
    ) -> dict[str, list[dict[str, Any]]]:
        results = {}

        if connection_type in ["both", "incoming"]:
            results["incoming"] = self.scrape_incoming_connections(max_results)

        if connection_type in ["both", "outgoing"]:
            results["outgoing"] = self.scrape_outgoing_connections(max_results)

        return results

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

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            self.human_behavior.delay(1, 2)

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

    def _wait_for_page_load(self) -> bool:
        try:
            self.wait.until(lambda driver: driver.current_url != "about:blank")
            return "linkedin.com/in/" in self.driver.current_url
        except TimeoutException:
            return False

    def _click_connect_button(self) -> bool:
        direct_connect_selectors = [
            "section.artdeco-card[data-member-id] .artdeco-dropdown__item[aria-label^='Invite'][aria-label$='connect']",
            "div.pv-s-profile-actions button[aria-label*='Invite'][aria-label*='connect']",
            "div.ph5.pb5 button[aria-label*='Invite'][aria-label*='connect']",
            "main section.artdeco-card button[aria-label*='Invite'][aria-label*='connect']",
            "button.artdeco-button.artdeco-button--2.artdeco-button--primary[aria-label*='Invite']",
            "button[data-control-name='connect']",
        ]

        for selector in direct_connect_selectors:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed() and button.is_enabled():
                    print(selector)
                    aria_label = button.get_attribute("aria-label") or ""
                    data_control = button.get_attribute("data-control-name") or ""
                    if (
                        "connect" in aria_label.lower() and "invite" in aria_label.lower()
                    ) or data_control == "connect":
                        self.human_behavior.delay(0.5, 1.0)
                        button.click()
                        return True
            except (NoSuchElementException, Exception):
                continue

        return self._try_dropdown_connect()

    def _try_dropdown_connect(self) -> bool:
        dropdown_selectors = [
            "section[data-view-name='profile-card'] button[aria-label*='More actions']",
            "div.pv-s-profile-actions button[aria-label*='More actions']",
            "div.ph5.pb5 button[aria-label*='More actions']",
            "main section.artdeco-card button[aria-label*='More actions']",
            "button.artdeco-dropdown__trigger[aria-label*='More actions']",
            "button[data-view-name='profile-overflow-button']",
        ]

        for selector in dropdown_selectors:
            try:
                dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                if dropdown.is_displayed() and dropdown.is_enabled():
                    self.human_behavior.delay(0.5, 1.0)
                    try:
                        dropdown.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", dropdown)

                    self.human_behavior.delay(2.0, 3.0)

                    if self._click_dropdown_connect():
                        return True

            except (NoSuchElementException, Exception):
                continue

        return False

    def _click_dropdown_connect(self) -> bool:
        try:
            WebDriverWait(self.driver, 5).until(
                EC.any_of(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "div[data-view-name='edge-creation-connect-action'], a[href*='custom-invite'], div[aria-label*='Invite'][aria-label*='connect']",
                        )
                    ),
                )
            )
        except TimeoutException:
            return False

        connect_selectors = [
            "div.artdeco-dropdown div[aria-label^='Invite'][aria-label$='connect']",
            ".artdeco-dropdown__item[aria-label*='connect']",
        ]

        for selector in connect_selectors:
            try:
                connect_items = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for connect_item in connect_items:
                    if connect_item.is_displayed():
                        self.human_behavior.delay(0.5, 1)

                        try:
                            connect_item.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", connect_item)

                        self.human_behavior.delay(1, 2)

                        with contextlib.suppress(TimeoutException):
                            self.wait.until_not(
                                EC.visibility_of_element_located(
                                    (By.CSS_SELECTOR, ".artdeco-dropdown__content")
                                )
                            )

                        return True

            except (NoSuchElementException, Exception):
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

        for selector in modal_selectors:
            try:
                modal = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                self.wait.until(EC.visibility_of(modal))
                return True
            except TimeoutException:
                continue

        return False

    def _send_with_note(self, note: str) -> bool:
        try:
            add_note_selectors = [
                "button[aria-label*='Add a note']",
                "button[aria-label*='Add a free note']",
                "div.artdeco-modal button[data-control-name='add_note']",
                "div.send-invite button.artdeco-button--muted",
            ]

            add_note_button = None
            for selector in add_note_selectors:
                try:
                    add_note_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not add_note_button:
                return False

            add_note_button.click()

            textarea_selectors = [
                "div.artdeco-modal textarea[name='message']",
                "div.send-invite textarea",
                "textarea[placeholder*='Add a note']",
                "div.artdeco-modal textarea",
            ]

            textarea = None
            for selector in textarea_selectors:
                try:
                    textarea = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not textarea:
                return False

            textarea.clear()
            self.human_behavior.type_text(textarea, note)

            send_button_selectors = [
                "button[aria-label*='Send invitation']",
                "div.artdeco-modal button[data-control-name='send']",
                "div.send-invite button.artdeco-button--primary",
                "button.artdeco-button--primary[type='submit']",
            ]

            send_button = None
            for selector in send_button_selectors:
                try:
                    send_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not send_button:
                return False

            send_button.click()

            self.log_action("SUCCESS", "Connection request sent with note")
            return True

        except Exception as e:
            self.log_action("ERROR", f"Failed to send with note: {e!s}")
            return False

    def _send_without_note(self) -> bool:
        try:
            send_button_selectors = [
                "button[aria-label*='Send without a note']",
                "button[aria-label*='Send now']",
                "div.artdeco-modal button[data-control-name='send_without_note']",
                "div.send-invite button.artdeco-button--primary:not([aria-label*='Add'])",
                "button.artdeco-button--primary[type='submit']",
            ]

            send_button = None
            for selector in send_button_selectors:
                try:
                    send_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not send_button:
                return False

            send_button.click()

            self.log_action("SUCCESS", "Connection request sent without note")
            return True

        except Exception as e:
            self.log_action("ERROR", f"Failed to send without note: {e!s}")
            return False

    def _extract_incoming_connection_data(self, container: WebElement) -> dict[str, str] | None:
        data = {}

        try:
            name_link = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']:not([tabindex])")
            data["name"] = name_link.text.strip() or "N/A"
            data["profile_url"] = name_link.get_attribute("href") or "N/A"
        except:
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
        except:
            pass
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
        except:
            pass
        data["time_sent"] = time_text

        mutual_connections_text = "N/A"
        try:
            for p in paragraphs:
                txt = p.text.strip()
                if "mutual connection" in txt.lower():
                    mutual_connections_text = txt
                    break
        except:
            pass
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
        except:
            data["message"] = "N/A"

        try:
            img_element = container.find_element(By.CSS_SELECTOR, "img[alt*='profile picture']")
            data["image_url"] = img_element.get_attribute("src") or "N/A"
        except:
            data["image_url"] = "N/A"

        return data if data.get("name") != "N/A" else None

    def _extract_outgoing_connection_data(self, container: WebElement) -> dict[str, str] | None:
        data = {}

        try:
            name_link = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']:not([tabindex])")
            data["name"] = name_link.text.strip() or "N/A"
            data["profile_url"] = name_link.get_attribute("href") or "N/A"
        except:
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
        except:
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
        except:
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
        except:
            data["message"] = "N/A"

        try:
            img_element = container.find_element(By.CSS_SELECTOR, "img[alt*='profile picture']")
            data["image_url"] = img_element.get_attribute("src") or "N/A"
        except:
            data["image_url"] = "N/A"

        print(data)
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
        except:
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
            except:
                pass
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
