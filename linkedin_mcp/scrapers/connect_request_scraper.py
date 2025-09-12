import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ConnectRequestScraper:
    def __init__(self, driver, wait, human_behavior, tracking_handler):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.tracking_handler = tracking_handler

    def _is_valid_linkedin_url(self, url):
        if not url or not isinstance(url, str) or url == "N/A":
            return False
        linkedin_pattern = r'^https?://(www\.)?linkedin\.com/in/'
        return bool(re.match(linkedin_pattern, url))

    def send_connection_request(self, profile_url, note=None):
        if not self._is_valid_linkedin_url(profile_url):
            print(f"[ERROR] Invalid profile URL: {profile_url}")
            return False

        print(f"Sending connection request to: {profile_url}")

        try:
            self.driver.get(profile_url)
            
            if not self._wait_for_page_load():
                print("[ERROR] Failed to load profile page")
                return False

            self.human_behavior.human_delay(1, 2)

            if not self._click_connect_button():
                print("[ERROR] Connect button not found")
                return False

            if not self._wait_for_modal():
                print("[ERROR] Connection modal not found")
                return False

            if note and note.strip():
                return self._send_with_note(note)
            else:
                return self._send_without_note()

        except Exception as e:
            print(f"[ERROR] Connection request failed: {str(e)}")
            return False

    def _wait_for_page_load(self):
        try:
            self.wait.until(lambda driver: driver.current_url != "about:blank")
            return "linkedin.com/in/" in self.driver.current_url
        except TimeoutException:
            return False

    def _click_connect_button(self):
        direct_connect_selectors = [
            ".artdeco-card button[aria-label*='connect']",
            "a[aria-label*='Connect']",
        ]

        for selector in direct_connect_selectors:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed() and button.is_enabled():
                    aria_label = button.get_attribute("aria-label") or ""
                    if "connect" in aria_label.lower() or "invite" in aria_label.lower():
                        self.human_behavior.human_delay(0.5, 1)
                        button.click()
                        return True
            except (NoSuchElementException, Exception):
                continue

        return self._try_dropdown_connect()

    def _try_dropdown_connect(self):
        dropdown_selectors = [
            "div[componentkey*='Topcard'] button[aria-label*='More']",
            "div[componentkey*='Topcard'] button[data-view-name='profile-overflow-button']",
            "button[aria-label*='More']",
            "button[data-view-name='profile-overflow-button']"
        ]

        for selector in dropdown_selectors:
            try:
                dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                if dropdown.is_displayed() and dropdown.is_enabled():
                    self.human_behavior.human_delay(0.5, 1)
                    
                    try:
                        dropdown.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", dropdown)
                    
                    self.human_behavior.human_delay(2, 3)
                    
                    if self._click_dropdown_connect():
                        return True
                    
            except (NoSuchElementException, Exception):
                continue

        return False

    def _click_dropdown_connect(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-view-name='edge-creation-connect-action'], a[href*='custom-invite'], div[aria-label*='Invite'][aria-label*='connect']")),
                )
            )
        except TimeoutException:
            return False

        connect_selectors = [
            "div[aria-label*='Invite'][aria-label*='connect']",
            ".artdeco-dropdown__item[aria-label*='connect']",
        ]

        for selector in connect_selectors:
            try:
                connect_item = self.driver.find_element(By.CSS_SELECTOR, selector)
                if connect_item.is_displayed():
                    self.human_behavior.human_delay(0.5, 1)
                    connect_item.click()
                    self.human_behavior.human_delay(1, 2)
                    
                    try:
                        self.wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, ".artdeco-dropdown__content")))
                    except TimeoutException:
                        pass
                    
                    return True
            except (NoSuchElementException, Exception):
                continue

        return False

    def _wait_for_modal(self):
        modal_selectors = [
            "div.artdeco-modal[role='dialog']",
            "div[aria-labelledby*='send-invite']"
        ]

        for selector in modal_selectors:
            try:
                modal = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.wait.until(EC.visibility_of(modal))
                return True
            except TimeoutException:
                continue

        return False

    def _send_with_note(self, note):
        try:
            add_note_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Add a note'], button[aria-label*='Add a free note']"))
            )
            add_note_button.click()

            textarea = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea"))
            )
            textarea.clear()
            self.human_behavior.human_type(textarea, note)

            send_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Send invitation']"))
            )
            send_button.click()

            print("[SUCCESS] Connection request sent with note")
            return True

        except TimeoutException as e:
            print(f"[ERROR] Failed to send with note: {str(e)}")
            return False

    def _send_without_note(self):
        try:
            send_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Send without a note']"))
            )
            send_button.click()

            print("[SUCCESS] Connection request sent without note")
            return True

        except TimeoutException as e:
            print(f"[ERROR] Failed to send without note: {str(e)}")
            return False