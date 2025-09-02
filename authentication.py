import time
import os
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LinkedInAuth:
    def __init__(self, driver, wait, human_behavior, email=None, password=None, li_at_cookie=None, cookie_file="linkedin_cookies.pkl"):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.email = email
        self.password = password
        self.li_at_cookie = li_at_cookie
        self.cookie_file = cookie_file
        
    def authenticate(self):
        if self.load_cookies():
            try:
                self.driver.get("https://www.linkedin.com/feed/")
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                print("✅ Authentication successful using saved cookies!")
                return True
            except TimeoutException:
                print("⚠️ Saved cookies are expired, trying other methods...")
                
        if self.li_at_cookie:
            if self.authenticate_with_cookie():
                return True
                
        if self.email and self.password:
            if self.login_with_credentials():
                return True
                
        print("❌ All authentication methods failed!")
        raise Exception("Authentication failed")
        
    def save_cookies(self):
        cookies = self.driver.get_cookies()
        with open(self.cookie_file, 'wb') as file:
            pickle.dump(cookies, file)
        print(f"✅ Cookies saved to {self.cookie_file}")
        
        for cookie in cookies:
            if cookie['name'] == 'li_at':
                print(f"🔑 li_at cookie value: {cookie['value']}")
                with open('li_at_cookie.txt', 'w') as f:
                    f.write(cookie['value'])
                print("✅ li_at cookie saved to li_at_cookie.txt")
                break
                
    def load_cookies(self):
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'rb') as file:
                    cookies = pickle.load(file)
                    
                self.driver.get("https://www.linkedin.com")
                time.sleep(2)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Warning: Could not add cookie {cookie.get('name', 'unknown')}: {e}")
                        
                self.driver.refresh()
                time.sleep(3)
                
                print("✅ Cookies loaded from file")
                return True
            except Exception as e:
                print(f"❌ Error loading cookies: {e}")
                return False
        return False
        
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
                print("✅ Login successful!")
                self.save_cookies()
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
            
            self.driver.get("https://www.linkedin.com/feed/")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            print("✅ Cookie authentication successful!")
            return True
            
        except TimeoutException:
            print("❌ Cookie authentication failed. Cookie might be expired or invalid.")
            return False
        except Exception as e:
            print(f"❌ Error during cookie authentication: {str(e)}")
            return False
            
    def is_challenge_present(self):
        challenge_indicators = [
            "challenge", "verification", "captcha", "security-challenge", "checkpoint", "two-step"
        ]
        
        page_source = self.driver.page_source.lower()
        return any(indicator in page_source for indicator in challenge_indicators)
        
    def handle_challenge(self):
        print("\n🔒 Security challenge detected!")
        print("Please complete the challenge manually in the browser window.")
        print("This might include:")
        print("  - Email verification")
        print("  - Phone verification") 
        print("  - CAPTCHA")
        print("  - Two-factor authentication")
        
        input("\n⏳ After completing the challenge, press ENTER to continue...")
        
        self.human_behavior.human_delay(2, 4)
        
        current_url = self.driver.current_url
        if "feed" in current_url or "mynetwork" in current_url:
            print("✅ Challenge completed successfully!")
            self.save_cookies()
            return True
        else:
            self.driver.get("https://www.linkedin.com/feed/")
            self.human_behavior.human_delay(2, 4)
            
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                print("✅ Login verified after challenge!")
                self.save_cookies()
                return True
            except TimeoutException:
                print("❌ Login failed even after challenge completion")
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