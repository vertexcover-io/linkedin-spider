import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LinkedInAuth:
    def __init__(self, driver, wait, human_behavior, email=None, password=None, li_at_cookie=None):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.email = email
        self.password = password
        self.li_at_cookie = li_at_cookie
        
    def authenticate(self):
        if self.li_at_cookie:
            if self.authenticate_with_cookie():
                return True
                
        if self.email and self.password:
            if self.login_with_credentials():
                return True
                
        print("❌ All authentication methods failed!")
        raise Exception("Authentication failed")
        
        
    def login_with_credentials(self):
        print("Logging in with email and password...")
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            self.human_behavior.human_delay(2, 4)
            
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            self.human_behavior.human_click(email_field)
            self.human_behavior.human_type(email_field, self.email)
            
            password_field = self.driver.find_element(By.ID, "password")
            self.human_behavior.human_click(password_field)
            self.human_behavior.human_type(password_field, self.password)
            
            self.human_behavior.human_delay(1, 3)
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self.human_behavior.human_click(login_button)
            
            print("Login form submitted...")
            self.human_behavior.human_delay(3, 6)
            
            current_url = self.driver.current_url
            
            if "feed" in current_url or "mynetwork" in current_url:
                if self.verify_feed_access():
                    print("✅ Login successful!")
                    return True
            elif "challenge" in current_url or self.is_challenge_present():
                return self.handle_challenge()
            elif self.check_login_errors():
                return False
            else:
                print(f"❌ Unexpected page after login: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False
            
    def authenticate_with_cookie(self):
        print("Authenticating with li_at cookie...")
        
        try:
            self.driver.get("https://www.linkedin.com")
            self.human_behavior.human_delay(1, 3)
            
            self.driver.add_cookie({
                'name': 'li_at',
                'value': self.li_at_cookie,
                'domain': '.linkedin.com',
                'path': '/',
                'secure': True
            })
            
            self.driver.refresh()
            self.human_behavior.human_delay(2, 4)
            
            if not self._handle_welcome_back_page():
                return False
                
            return self._wait_for_feed_or_handle_challenge()
            
        except TimeoutException:
            print("❌ Cookie authentication failed. Cookie might be expired or invalid.")
            return False
        except Exception as e:
            print(f"❌ Error during cookie authentication: {str(e)}")
            return False
            
    def _wait_for_feed_or_handle_challenge(self):
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"🔄 Attempting to reach feed page (attempt {attempt}/{max_attempts})...")
            
            self.driver.get("https://www.linkedin.com/feed/")
            self.human_behavior.human_delay(3, 6)
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            if "challenge" in current_url or self.is_challenge_present():
                print("🔒 Challenge page detected!")
                if self.handle_challenge():
                    return True
                else:
                    continue
            
            if "feed" in current_url or "mynetwork" in current_url:
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                    if self.verify_feed_access():
                        print("✅ Successfully reached feed page!")
                        return True
                except TimeoutException:
                    print("⏳ Feed page elements not loaded yet, checking for challenges...")
                    if self.is_challenge_present():
                        print("🔒 Challenge detected during feed loading!")
                        if self.handle_challenge():
                            return True
                        else:
                            continue
            
            if "login" in current_url or "signin" in current_url:
                print("⚠️ Redirected to login page - authentication may have failed")
                return False
                
            print(f"⚠️ Not on feed page yet. Current URL: {current_url}")
            self.human_behavior.human_delay(2, 4)
        
        print("❌ Failed to reach feed page after multiple attempts")
        return False

    def is_challenge_present(self):
        current_url = self.driver.current_url.lower()
        
        challenge_url_indicators = [
            "challenge", "verification", "captcha", "security-challenge", "checkpoint", "two-step","uas/login"
        ]
        
        if any(indicator in current_url for indicator in challenge_url_indicators):
            return True
            
        return False
    
    def handle_challenge(self):
        print("\n🔒 Security challenge detected!")
        print("Please complete the challenge manually in the browser window.")
        
        max_challenge_attempts = 3
        attempt = 0
        
        while attempt < max_challenge_attempts:
            attempt += 1
            print(f"\n⏳ Challenge attempt {attempt}/{max_challenge_attempts}")
            print("After completing the challenge, press ENTER to continue...")
            
            input()
            
            self.human_behavior.human_delay(3, 6)
            
            current_url = self.driver.current_url.lower()

            print(f"Current URL: {current_url}")
            
            if "challenge" in current_url or self.is_challenge_present():
                print("⚠️ Challenge still present, please try again...")
                continue
            
            if "feed" in current_url or "mynetwork" in current_url:
                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                    if self.verify_feed_access():
                        print("✅ Challenge completed successfully!")
                        return True
                except TimeoutException:
                    print("⏳ Feed page loading, checking again...")
                    self.human_behavior.human_delay(2, 4)
                    if self.verify_feed_access():
                        print("✅ Challenge completed successfully!")
                        return True
            
            print("🔄 Navigating to feed page to verify authentication...")
            self.driver.get("https://www.linkedin.com/feed/")
            self.human_behavior.human_delay(3, 6)
            
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                if self.verify_feed_access():
                    print("✅ Authentication verified after challenge!")
                    return True
            except TimeoutException:
                print("⏳ Feed page not loading properly, checking for additional challenges...")
                if self.is_challenge_present():
                    print("🔒 Additional challenge detected!")
                    continue
        
        print("❌ Failed to complete challenge after multiple attempts")
        return False
                
    def check_login_errors(self):
        try:
            error_selectors = [
                ".form__label--error",
                ".alert", 
                "[data-js-module-id='guest-input-validation']",
                ".msg--error"
            ]
            
            for selector in error_selectors:
                try:
                    error_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if error_element.is_displayed():
                        print(f"❌ Login error: {error_element.text}")
                        return True
                except NoSuchElementException:
                    continue
                    
            return False
            
        except Exception:
            return False
            
    def verify_feed_access(self):
        try:
            current_url = self.driver.current_url.lower()
            
            if not ("feed" in current_url or "mynetwork" in current_url or "linkedin.com" in current_url):
                return False
                
            feed_indicators = [
                "main[role='main']",
                "[data-test-id='feed-container']",
                ".scaffold-layout__content",
                ".feed-container",
                "[data-view-name='feed-container']",
                ".global-nav__me",
                ".global-nav__me-photo",
                ".global-nav__primary",
                ".global-nav__secondary",
                "[data-test-id='global-nav']"
            ]
            
            for selector in feed_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
                    
            page_source = self.driver.page_source.lower()
            feed_keywords = [
                "start a post",
                "what's on your mind",
                "feed",
                "linkedin news",
                "trending",
                "suggested for you",
                "write a post",
                "share an article",
                "global navigation",
                "messaging",
                "notifications"
            ]
            
            if any(keyword in page_source for keyword in feed_keywords):
                return True
                
            challenge_indicators = [
                "challenge", "verification", "captcha", "security-challenge", 
                "checkpoint", "two-step", "verify your identity"
            ]
            
            if any(indicator in page_source for indicator in challenge_indicators):
                return False
                
            return False
            
        except Exception:
            return False
            
    def _handle_welcome_back_page(self):
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            welcome_indicators = [
                "welcome back",
                "choose your account",
                "select account",
                "which account",
                "continue as"
            ]
            
            if not any(indicator in page_source for indicator in welcome_indicators):
                return True
            
            print("🔍 Welcome back page detected, selecting profile...")
            
            profile_selectors = [
                "button[data-test-id='profile-selector']",
                ".profile-selector button",
                ".account-selector button",
                "button[aria-label*='profile']",
                ".profile-card button",
                "button:contains('Continue')",
                ".profile-selector .profile-card"
            ]
            
            for selector in profile_selectors:
                try:
                    if "contains" in selector:
                        continue
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        first_button = elements[0]
                        if first_button.is_displayed() and first_button.is_enabled():
                            self.human_behavior.human_click(first_button)
                            self.human_behavior.human_delay(2, 4)
                            
                            if self.verify_feed_access():
                                print("✅ Profile selected successfully!")
                                return True
                            else:
                                self.driver.get("https://www.linkedin.com/feed/")
                                self.human_behavior.human_delay(2, 4)
                                return self.verify_feed_access()
                except Exception:
                    continue
            
            xpath_selectors = [
                "//button[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Select')]",
                "//div[contains(@class, 'profile')]//button",
                "//button[contains(@aria-label, 'profile')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        first_button = elements[0]
                        if first_button.is_displayed() and first_button.is_enabled():
                            self.human_behavior.human_click(first_button)
                            self.human_behavior.human_delay(2, 4)
                            
                            if self.verify_feed_access():
                                print("✅ Profile selected successfully!")
                                return True
                            else:
                                self.driver.get("https://www.linkedin.com/feed/")
                                self.human_behavior.human_delay(2, 4)
                                return self.verify_feed_access()
                except Exception:
                    continue
            
            print("⚠️ Could not find profile selector, trying direct navigation...")
            self.driver.get("https://www.linkedin.com/feed/")
            self.human_behavior.human_delay(2, 4)
            return self.verify_feed_access()
            
        except Exception as e:
            print(f"❌ Error handling welcome back page: {e}")
            return False