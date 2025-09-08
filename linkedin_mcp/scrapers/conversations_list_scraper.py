import random
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ConversationsListScraper:
    def __init__(self, driver, wait, human_behavior, tracking_handler):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.tracking_handler = tracking_handler
    
    def scrape_conversations_list(self, max_results=50):
        try:
            self.driver.get("https://www.linkedin.com/messaging/")
            self.human_behavior.human_delay(2, 4)
            
            self._load_conversations(max_results)
            
            conversations = []
            conversation_items = self.driver.find_elements(By.CSS_SELECTOR, "li.msg-conversation-listitem")
            
            for item in conversation_items[:max_results]:
                conversation = self._extract_conversation_item(item)
                if conversation:
                    conversations.append(conversation)
            
            return conversations[:max_results]
            
        except Exception as e:
            print(f"[ERROR] Error scraping conversations list: {str(e)}")
            return []
    
    def _load_conversations(self, max_results):
        try:
            scroll_container = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".msg-conversations-container--inbox-shortcuts"))
            )
            
            previous_count = 0
            stable_count = 0
            max_stable = 3
            max_attempts = 15
            
            for attempt in range(max_attempts):
                conversation_items = self.driver.find_elements(By.CSS_SELECTOR, "li.msg-conversation-listitem")
                loaded_conversations = [item for item in conversation_items if self._has_conversation_content(item)]
                current_count = len(loaded_conversations)
                
                print(f"[INFO] Attempt {attempt + 1}: {current_count} conversations with content (need {max_results})")
                
                if current_count >= max_results:
                    print(f"[INFO] Required {max_results} conversations loaded")
                    break
                
                if current_count == previous_count:
                    stable_count += 1
                    if stable_count >= max_stable:
                        print(f"[INFO] No more conversations available, got {current_count}")
                        break
                else:
                    stable_count = 0
                    previous_count = current_count
                
                conversations_list = self.driver.find_element(By.CSS_SELECTOR, "ul.msg-conversations-container__conversations-list")
                self.driver.execute_script("""
                    arguments[0].scrollTop = arguments[0].scrollHeight;
                """, conversations_list)
                
                self.human_behavior.human_delay(2, 3)
                
        except Exception as e:
            print(f"[ERROR] Error loading conversations: {str(e)}")
    
    def _has_conversation_content(self, item):
        try:
            name_element = item.find_element(By.CSS_SELECTOR, ".msg-conversation-listitem__participant-names span.truncate")
            message_element = item.find_element(By.CSS_SELECTOR, ".msg-conversation-card__message-snippet")
            return (name_element and name_element.text.strip() and 
                   message_element and message_element.text.strip())
        except:
            return False
    
    def _extract_conversation_item(self, item):
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
                'participant_name': participant_name,
                'profile_image_url': profile_image_url,
                'profile_url': profile_url,
                'timestamp': timestamp,
                'message_snippet': message_snippet,
                'is_sponsored': is_sponsored,
                'is_active': is_active,
                'online_status': online_status
            }
        except Exception:
            return None
    
    def _extract_participant_name(self, item):
        try:
            element = item.find_element(By.CSS_SELECTOR, ".msg-conversation-listitem__participant-names span.truncate")
            return element.text.strip()
        except NoSuchElementException:
            return "N/A"
    
    def _extract_profile_image(self, item):
        try:
            selectors = [
                "img.msg-facepile-grid__img--person",
                "img.presence-entity__image",
                "img.evi-image"
            ]
            
            for selector in selectors:
                try:
                    img_element = item.find_element(By.CSS_SELECTOR, selector)
                    return img_element.get_attribute('src')
                except NoSuchElementException:
                    continue
            return None
        except Exception:
            return None
    
    def _extract_profile_url(self, item):
        try:
            link_element = item.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            return link_element.get_attribute('href')
        except NoSuchElementException:
            return None
    
    def _extract_timestamp(self, item):
        try:
            timestamp_element = item.find_element(By.CSS_SELECTOR, "time.msg-conversation-card__time-stamp")
            return timestamp_element.text.strip()
        except NoSuchElementException:
            return None
    
    def _extract_message_snippet(self, item):
        try:
            snippet_element = item.find_element(By.CSS_SELECTOR, "p.msg-conversation-card__message-snippet")
            return snippet_element.text.strip()
        except NoSuchElementException:
            return None
    
    def _is_sponsored(self, item):
        try:
            item.find_element(By.CSS_SELECTOR, "span.msg-conversation-card__pill")
            return True
        except NoSuchElementException:
            return False
    
    def _is_active(self, item):
        try:
            item.find_element(By.CSS_SELECTOR, ".msg-conversations-container__convo-item-link--active")
            return True
        except NoSuchElementException:
            return False
    
    def _extract_online_status(self, item):
        try:
            presence_indicator = item.find_element(By.CSS_SELECTOR, "div.presence-indicator")
            class_list = presence_indicator.get_attribute('class')
            
            if 'presence-indicator--is-reachable' in class_list:
                return 'online'
            elif 'hidden' in class_list:
                return 'offline'
            return 'unknown'
        except NoSuchElementException:
            return None