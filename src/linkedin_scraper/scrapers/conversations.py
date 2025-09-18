import difflib
import re
from typing import Any

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from .base import BaseScraper


class ConversationScraper(BaseScraper):
    """Scraper for LinkedIn conversations and messages."""

    def _find_element_in_parent(self, parent: WebElement, by: By, value: str) -> WebElement | None:
        """Find element within parent element."""
        try:
            return parent.find_element(by, value)
        except Exception:
            return None

    def scrape_conversations_list(self, max_results: int = 50) -> list[dict[str, Any]]:
        """Scrape list of conversations."""
        try:
            self.driver.get("https://www.linkedin.com/messaging/")
            self.human_behavior.delay(2, 4)

            self._load_conversations(max_results)

            conversations = []
            conversation_items = self.driver.find_elements(
                By.CSS_SELECTOR, "li.msg-conversation-listitem"
            )

            for item in conversation_items[:max_results]:
                conversation = self._extract_conversation_item(item)
                if conversation:
                    conversations.append(conversation)

            return conversations[:max_results]

        except Exception as e:
            self.log_action("ERROR", f"Error scraping conversations list: {e!s}")
            return []

    def scrape_conversation_messages(
        self, participant_name: str | None = None
    ) -> dict[str, Any] | None:
        """Scrape messages from a specific conversation."""
        try:
            if participant_name:
                self._navigate_to_conversation_by_name(participant_name)
            else:
                self.driver.get("https://www.linkedin.com/messaging/")

            self.human_behavior.delay(2, 4)

            self._load_all_messages()

            messages = []
            message_items = self.driver.find_elements(
                By.CSS_SELECTOR, "li.msg-s-message-list__event"
            )

            for item in message_items:
                message = self._extract_message_item(item)
                if message:
                    messages.append(message)

            return {"messages": messages, "total_messages": len(messages)}

        except Exception as e:
            self.log_action("ERROR", f"Error scraping conversation messages: {e!s}")
            return {"messages": [], "total_messages": 0}

    def _load_conversations(self, max_results: int) -> None:
        try:
            scroll_container = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".msg-conversations-container--inbox-shortcuts")
                )
            )

            previous_count = 0
            stable_count = 0
            max_stable = 3
            max_attempts = 15

            for attempt in range(max_attempts):
                conversation_items = self.driver.find_elements(
                    By.CSS_SELECTOR, "li.msg-conversation-listitem"
                )
                loaded_conversations = [
                    item for item in conversation_items if self._has_conversation_content(item)
                ]
                current_count = len(loaded_conversations)

                self.log_action(
                    "INFO",
                    f"Attempt {attempt + 1}: {current_count} conversations with content (need {max_results})",
                )

                if current_count >= max_results:
                    self.log_action("INFO", f"Required {max_results} conversations loaded")
                    break

                if current_count == previous_count:
                    stable_count += 1
                    if stable_count >= max_stable:
                        self.log_action(
                            "INFO", f"No more conversations available, got {current_count}"
                        )
                        break
                else:
                    stable_count = 0
                    previous_count = current_count

                conversations_list = self.driver.find_element(
                    By.CSS_SELECTOR, "ul.msg-conversations-container__conversations-list"
                )
                self.driver.execute_script(
                    """
                    arguments[0].scrollTop = arguments[0].scrollHeight;
                """,
                    conversations_list,
                )

                self.human_behavior.delay(2, 3)

        except Exception as e:
            self.log_action("ERROR", f"Error loading conversations: {e!s}")

    def _has_conversation_content(self, item: WebElement) -> bool:
        try:
            name_element = item.find_element(
                By.CSS_SELECTOR, ".msg-conversation-listitem__participant-names span.truncate"
            )
            message_element = item.find_element(
                By.CSS_SELECTOR, ".msg-conversation-card__message-snippet"
            )
            return (
                name_element
                and name_element.text.strip()
                and message_element
                and message_element.text.strip()
            )
        except:
            return False

    def _extract_conversation_item(self, item: WebElement) -> dict[str, Any] | None:
        try:
            if not self._has_conversation_content(item):
                return None

            participant_name = self._extract_participant_name(item)
            profile_image_url = self._extract_profile_image(item)
            profile_url = self._extract_profile_url(item)
            timestamp = self._extract_timestamp(item)
            message_snippet = self._extract_message_snippet(item)
            is_sponsored = self._is_sponsored(item)
            is_active = self._is_active(item)
            online_status = self._extract_online_status(item)

            return {
                "participant_name": participant_name,
                "profile_image_url": profile_image_url,
                "profile_url": profile_url,
                "timestamp": timestamp,
                "message_snippet": message_snippet,
                "is_sponsored": is_sponsored,
                "is_active": is_active,
                "online_status": online_status,
            }
        except Exception:
            return None

    def _extract_participant_name(self, item: WebElement) -> str:
        try:
            element = item.find_element(
                By.CSS_SELECTOR, ".msg-conversation-listitem__participant-names span.truncate"
            )
            return element.text.strip()
        except NoSuchElementException:
            return "N/A"

    def _extract_profile_image(self, item: WebElement) -> str | None:
        try:
            selectors = [
                "img.msg-facepile-grid__img--person",
                "img.presence-entity__image",
                "img.evi-image",
            ]

            for selector in selectors:
                try:
                    img_element = item.find_element(By.CSS_SELECTOR, selector)
                    return img_element.get_attribute("src")
                except NoSuchElementException:
                    continue
            return None
        except Exception:
            return None

    def _extract_profile_url(self, item: WebElement) -> str | None:
        try:
            link_element = item.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            return link_element.get_attribute("href")
        except NoSuchElementException:
            return None

    def _extract_timestamp(self, item: WebElement) -> str | None:
        try:
            timestamp_element = item.find_element(
                By.CSS_SELECTOR, "time.msg-conversation-card__time-stamp"
            )
            return timestamp_element.text.strip()
        except NoSuchElementException:
            return None

    def _extract_message_snippet(self, item: WebElement) -> str | None:
        try:
            snippet_element = item.find_element(
                By.CSS_SELECTOR, "p.msg-conversation-card__message-snippet"
            )
            return snippet_element.text.strip()
        except NoSuchElementException:
            return None

    def _is_sponsored(self, item: WebElement) -> bool:
        try:
            item.find_element(By.CSS_SELECTOR, "span.msg-conversation-card__pill")
            return True
        except NoSuchElementException:
            return False

    def _is_active(self, item: WebElement) -> bool:
        try:
            item.find_element(
                By.CSS_SELECTOR, ".msg-conversations-container__convo-item-link--active"
            )
            return True
        except NoSuchElementException:
            return False

    def _extract_online_status(self, item: WebElement) -> str | None:
        try:
            presence_indicator = item.find_element(By.CSS_SELECTOR, "div.presence-indicator")
            class_list = presence_indicator.get_attribute("class")

            if "presence-indicator--is-reachable" in class_list:
                return "online"
            elif "hidden" in class_list:
                return "offline"
            return "unknown"
        except NoSuchElementException:
            return None

    def _navigate_to_conversation_by_name(self, participant_name: str) -> None:
        try:
            self.driver.get("https://www.linkedin.com/messaging/")
            self.human_behavior.delay(2, 4)

            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#search-conversations"))
            )

            search_input.clear()
            search_input.send_keys(participant_name)
            self.human_behavior.delay(1, 2)

            from selenium.webdriver.common.keys import Keys

            search_input.send_keys(Keys.ENTER)
            self.human_behavior.delay(3, 5)

            conversation_items = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "li.msg-conversation-listitem")
                )
            )

            if not conversation_items:
                raise Exception("No search results found")

            best_match = self._find_best_search_match(conversation_items, participant_name)

            if not best_match:
                raise Exception(f"No suitable match found for '{participant_name}'")

            conversation_item, similarity_score = best_match
            self.log_action("INFO", f"Found best match with {similarity_score:.2f} similarity")

            conversation_item.click()
            self.human_behavior.delay(2, 4)

        except Exception as e:
            self.log_action("ERROR", f"Error navigating to conversation: {e!s}")
            raise

    def _find_best_search_match(
        self, conversation_items: list[WebElement], target_name: str
    ) -> tuple[WebElement, float] | None:
        candidates = []
        target_name_clean = self._clean_name(target_name)

        for item in conversation_items:
            try:
                name_element = item.find_element(
                    By.CSS_SELECTOR, ".msg-conversation-listitem__participant-names span.truncate"
                )
                if name_element and name_element.text.strip():
                    conversation_name = name_element.text.strip()
                    conversation_name_clean = self._clean_name(conversation_name)

                    similarity = difflib.SequenceMatcher(
                        None, target_name_clean, conversation_name_clean
                    ).ratio()

                    if similarity > 0.3:
                        candidates.append((item, similarity, conversation_name))

            except NoSuchElementException:
                continue

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        best_match = candidates[0]

        self.log_action("INFO", f"Best match: '{best_match[2]}' (similarity: {best_match[1]:.2f})")

        if len(candidates) > 1:
            self.log_action(
                "INFO", f"Other matches found: {[(name, sim) for _, sim, name in candidates[1:3]]}"
            )

        return (best_match[0], best_match[1])

    def _clean_name(self, name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9\s]", "", name.lower().strip())

    def _load_all_messages(self) -> None:
        try:
            scroll_container = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".msg-s-message-list.msg-s-message-list--scroll-buffer")
                )
            )
            self._scroll_to_conversation_beginning(scroll_container)

        except Exception as e:
            self.log_action("ERROR", f"Error loading all messages: {e!s}")

    def _scroll_to_conversation_beginning(self, scroll_container: WebElement) -> None:
        try:
            self.log_action("INFO", "Starting to scroll and load all messages...")

            previous_message_count = 0
            stable_count = 0
            max_stable = 3
            max_attempts = 30

            for attempt in range(max_attempts):
                current_messages = len(
                    self.driver.find_elements(By.CSS_SELECTOR, "li.msg-s-message-list__event")
                )
                loaded_messages = len(
                    self.driver.find_elements(
                        By.CSS_SELECTOR, "li.msg-s-message-list__event p.msg-s-event-listitem__body"
                    )
                )

                self.log_action(
                    "INFO",
                    f"Attempt {attempt + 1}: {current_messages} total, {loaded_messages} with text",
                )

                if current_messages == previous_message_count:
                    stable_count += 1
                    if stable_count >= max_stable:
                        self.log_action("INFO", "Message count stable, all loaded")
                        break
                else:
                    stable_count = 0
                    previous_message_count = current_messages

                self.driver.execute_script(
                    """
                    arguments[0].scrollTo({
                        top: 0,
                        behavior: 'auto'
                    });
                """,
                    scroll_container,
                )

                self.human_behavior.delay(2, 4)

                self.driver.execute_script(
                    """
                    arguments[0].scrollTo({
                        top: -999999,
                        behavior: 'auto'
                    });
                """,
                    scroll_container,
                )

                self.human_behavior.delay(1.5, 2.5)

            final_count = len(
                self.driver.find_elements(By.CSS_SELECTOR, "li.msg-s-message-list__event")
            )
            final_loaded = len(
                self.driver.find_elements(
                    By.CSS_SELECTOR, "li.msg-s-message-list__event p.msg-s-event-listitem__body"
                )
            )
            self.log_action(
                "INFO", f"Final: {final_count} total messages, {final_loaded} with content loaded"
            )

        except Exception as e:
            self.log_action("ERROR", f"Error in scroll process: {e!s}")

    def _extract_message_item(self, item: WebElement) -> dict[str, Any] | None:
        try:
            event_listitem = item.find_element(By.CSS_SELECTOR, "div.msg-s-event-listitem")
            if not event_listitem:
                return None

            message_text = self._extract_message_text(event_listitem)
            if not message_text or not message_text.strip():
                return None

            sender_name = self._extract_sender_name(event_listitem)
            sender_profile_image = self._extract_sender_profile_image(event_listitem)
            sender_profile_url = self._extract_sender_profile_url(event_listitem)
            timestamp = self._extract_message_timestamp(event_listitem)
            attachments = self._extract_attachments(event_listitem)
            is_sent = self._is_message_sent(event_listitem)
            message_urn = self._extract_message_urn(event_listitem)
            is_premium = self._is_premium_user(event_listitem)
            is_verified = self._is_verified_user(event_listitem)
            pronouns = self._extract_pronouns(event_listitem)

            return {
                "sender_name": sender_name,
                "sender_profile_image": sender_profile_image,
                "sender_profile_url": sender_profile_url,
                "timestamp": timestamp,
                "message_text": message_text,
                "attachments": attachments,
                "is_sent": is_sent,
                "message_urn": message_urn,
                "is_premium": is_premium,
                "is_verified": is_verified,
                "pronouns": pronouns,
            }
        except Exception:
            return None

    def _extract_sender_name(self, event_element: WebElement) -> str:
        try:
            name_element = event_element.find_element(
                By.CSS_SELECTOR, "span.msg-s-message-group__name"
            )
            return name_element.text.strip()
        except NoSuchElementException:
            return "N/A"

    def _extract_sender_profile_image(self, event_element: WebElement) -> str | None:
        try:
            img_element = event_element.find_element(
                By.CSS_SELECTOR, "img.msg-s-event-listitem__profile-picture"
            )
            return img_element.get_attribute("src")
        except NoSuchElementException:
            return None

    def _extract_sender_profile_url(self, event_element: WebElement) -> str | None:
        try:
            link_element = event_element.find_element(
                By.CSS_SELECTOR, "a.msg-s-event-listitem__link"
            )
            return link_element.get_attribute("href")
        except NoSuchElementException:
            return None

    def _extract_message_timestamp(self, event_element: WebElement) -> str | None:
        try:
            timestamp_element = event_element.find_element(
                By.CSS_SELECTOR, "time.msg-s-message-group__timestamp"
            )
            return timestamp_element.text.strip()
        except NoSuchElementException:
            return None

    def _extract_message_text(self, event_element: WebElement) -> str | None:
        try:
            message_element = event_element.find_element(
                By.CSS_SELECTOR, "p.msg-s-event-listitem__body"
            )
            return message_element.text.strip()
        except NoSuchElementException:
            return None

    def _extract_attachments(self, event_element: WebElement) -> list[dict[str, Any]]:
        attachments = []
        try:
            article_element = event_element.find_element(
                By.CSS_SELECTOR, "article.update-components-article"
            )

            title = self._extract_attachment_title(article_element)
            subtitle = self._extract_attachment_subtitle(article_element)
            url = self._extract_attachment_url(article_element)
            image_url = self._extract_attachment_image(article_element)

            attachments.append(
                {
                    "type": "article",
                    "title": title,
                    "subtitle": subtitle,
                    "url": url,
                    "image_url": image_url,
                }
            )
        except NoSuchElementException:
            pass

        return attachments

    def _extract_attachment_title(self, article_element: WebElement) -> str | None:
        try:
            title_element = article_element.find_element(
                By.CSS_SELECTOR, "div.update-components-article__title"
            )
            return title_element.text.strip()
        except NoSuchElementException:
            return None

    def _extract_attachment_subtitle(self, article_element: WebElement) -> str | None:
        try:
            subtitle_element = article_element.find_element(
                By.CSS_SELECTOR, "span[class*='update-components-article__subtitle--low-emphasis']"
            )
            return subtitle_element.text.strip()
        except NoSuchElementException:
            return None

    def _extract_attachment_url(self, article_element: WebElement) -> str | None:
        try:
            link_element = article_element.find_element(By.CSS_SELECTOR, "a[href]")
            return link_element.get_attribute("href")
        except NoSuchElementException:
            return None

    def _extract_attachment_image(self, article_element: WebElement) -> str | None:
        try:
            img_element = article_element.find_element(By.CSS_SELECTOR, "img")
            return img_element.get_attribute("src")
        except NoSuchElementException:
            return None

    def _is_message_sent(self, event_element: WebElement) -> bool:
        try:
            event_element.find_element(
                By.CSS_SELECTOR, "span.msg-s-event-with-indicator__sending-indicator--sent"
            )
            return True
        except NoSuchElementException:
            return False

    def _extract_message_urn(self, event_element: WebElement) -> str | None:
        return event_element.get_attribute("data-event-urn")

    def _is_premium_user(self, event_element: WebElement) -> bool:
        try:
            event_element.find_element(By.CSS_SELECTOR, "svg[aria-label='LinkedIn Premium']")
            return True
        except NoSuchElementException:
            return False

    def _is_verified_user(self, event_element: WebElement) -> bool:
        try:
            event_element.find_element(By.CSS_SELECTOR, "svg[aria-label='LinkedIn Verified']")
            return True
        except NoSuchElementException:
            return False

    def _extract_pronouns(self, event_element: WebElement) -> str | None:
        try:
            pronoun_elements = event_element.find_elements(By.CSS_SELECTOR, "span")
            for element in pronoun_elements:
                text = element.text.strip()
                if text.startswith("(") and text.endswith(")"):
                    return text
            return None
        except Exception:
            return None

    def scrape(self, *args, **kwargs) -> Any:
        """Main scraping implementation."""
        return self.scrape_conversations_list(*args, **kwargs)
