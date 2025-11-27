import logging
import os

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from linkedin_spider.core.driver import DriverManager
from linkedin_spider.utils.human_behavior import HumanBehavior

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles LinkedIn authentication via cookies or credentials."""

    def __init__(
        self,
        driver_manager: DriverManager,
        human_behavior: HumanBehavior,
        email: str | None = None,
        password: str | None = None,
        li_at_cookie: str | None = None,
    ):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver
        self.wait = driver_manager.wait
        self.human_behavior = human_behavior
        self.email = email
        self.password = password
        self.li_at_cookie = li_at_cookie

    def authenticate(self) -> bool:
        """
        Authenticate using available methods with smart fallback priority.

        Priority order:
        1. Try li_at_cookie from parameter (if provided)
        2. Check if already authenticated
        3. Try credentials from parameters (if provided)
        4. Raise error if no authentication method available

        Returns:
            bool: True if authentication succeeded

        Raises:
            Exception: If all authentication methods fail or no credentials provided
        """

        # Priority 1: If cookie parameter is explicitly provided, use it

        if self.li_at_cookie:
            logger.info("Using LinkedIn cookie from parameter")
            if self._authenticate_with_cookie(self.li_at_cookie):
                self.driver_manager.save_cookies()
                return True
            else:
                logger.error("Cookie from parameter failed")
                raise Exception("Provided li_at cookie is invalid or expired")

        # Priority 2: Check if already authenticated with saved cookies
        logger.info("Checking for saved cookies in profile directory...")
        if self._try_saved_cookies():
            logger.info("Successfully authenticated using saved cookies")
            return True
        else:
            logger.info("No valid saved cookies found or authentication failed")

        # Priority 3: Try credentials from parameters if provided
        if self.email and self.password:
            logger.info("Using LinkedIn credentials from parameter")
            if self._login_with_credentials(self.email, self.password):
                self.driver_manager.save_cookies()
                return True
            else:
                logger.error("Login with provided credentials failed")
                raise Exception("Login failed with provided credentials")

        # No authentication method available
        logger.error("No valid authentication method found")
        raise Exception(
            "Authentication required. Saved cookies not found or invalid. Please provide either:\n"
            "  - li_at cookie (--cookie parameter)\n"
            "  - Email and password (--email and --password parameters)\n"
            "  - Set environment variables: LINKEDIN_EMAIL, LINKEDIN_PASSWORD, or cookie"
        )

    def _is_authenticated(self) -> bool:
        """Check if already authenticated by examining current page."""
        try:
            current_url = self.driver.current_url.lower()

            if not current_url or "linkedin.com" not in current_url:
                self.driver.get("https://www.linkedin.com")
                self.human_behavior.delay(1, 2)
                current_url = self.driver.current_url.lower()

            if "login" in current_url or "signin" in current_url:
                return False

            if "feed" in current_url or "mynetwork" in current_url:
                return self._quick_feed_check()

            self.driver.get("https://www.linkedin.com")
            self.human_behavior.delay(1, 2)
            current_url = self.driver.current_url.lower()

            return (
                "login" not in current_url
                and "signin" not in current_url
                and self._quick_feed_check()
            )
        except Exception:
            return False

    def _quick_feed_check(self) -> bool:
        """Quick check for authentication indicators on current page."""
        try:
            page_source = self.driver.page_source.lower()
            auth_indicators = [
                "global-nav__me",
                "global-nav__primary",
                "messaging",
                "notifications",
                "start a post",
                "global navigation",
            ]
            return any(indicator in page_source for indicator in auth_indicators)
        except Exception:
            return False

    def _try_saved_cookies(self) -> bool:
        """Try to authenticate with saved cookies."""
        if not self.driver_manager.load_cookies():
            return False

        self.driver.get("https://www.linkedin.com")
        self.human_behavior.delay(1, 2)

        return self._is_authenticated()

    def _authenticate_with_cookie(self, cookie: str) -> bool:
        """
        Authenticate using li_at cookie with improved validation.

        Args:
            cookie: LinkedIn session cookie value

        Returns:
            bool: True if authentication succeeded
        """
        try:
            # Use the improved login_with_cookie method from driver_manager
            success = self.driver_manager.login_with_cookie(cookie)

            if success:
                self.human_behavior.delay(1, 2)
                self._handle_welcome_page()
                return self._is_authenticated()

            return False

        except Exception as e:
            logger.error(f"Cookie authentication exception: {e}")
            return False

    def _login_with_credentials(self, email: str, password: str) -> bool:
        """
        Login using email and password.

        Args:
            email: LinkedIn email
            password: LinkedIn password

        Returns:
            bool: True if login succeeded
        """
        try:
            self.driver.get("https://www.linkedin.com/login")
            self.human_behavior.delay(2, 3)

            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            self.human_behavior.click(email_field)
            self.human_behavior.type_text(email_field, email)

            password_field = self.driver.find_element(By.ID, "password")
            self.human_behavior.click(password_field)
            self.human_behavior.type_text(password_field, password)

            self.human_behavior.delay()

            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            self.human_behavior.click(login_button)

            self.human_behavior.delay(3, 5)

            if self._check_login_errors():
                logger.error("Login errors detected")
                return False

            if self._is_challenge_present():
                return self._handle_challenge()

            return self._is_authenticated()

        except Exception as e:
            logger.error(f"Credential login exception: {e}")
            return False

    def _is_challenge_present(self) -> bool:
        """Check if security challenge is present."""
        current_url = self.driver.current_url.lower()
        challenge_indicators = [
            "challenge",
            "verification",
            "captcha",
            "security-challenge",
            "checkpoint",
            "two-step",
            "uas/login",
        ]
        return any(indicator in current_url for indicator in challenge_indicators)

    def _handle_challenge(self) -> bool:
        """Handle security challenges with user interaction."""
        print("\n🔒 Security challenge detected!")
        print("Please complete the challenge manually in the browser window.")

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            print(f"\n[WAIT] Challenge attempt {attempt}/{max_attempts}")
            print("After completing the challenge, press ENTER to continue...")

            input()
            self.human_behavior.delay(3, 6)

            current_url = self.driver.current_url.lower()

            if not ("challenge" in current_url or self._is_challenge_present()):
                if "feed" in current_url or "mynetwork" in current_url:
                    try:
                        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                        if self._verify_feed_access():
                            print("[SUCCESS] Challenge completed successfully!")
                            return True
                    except TimeoutException:
                        pass

                self.driver.get("https://www.linkedin.com/feed/")
                self.human_behavior.delay(3, 6)

                try:
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                    if self._verify_feed_access():
                        print("[SUCCESS] Authentication verified after challenge!")
                        return True
                except TimeoutException:
                    if not self._is_challenge_present():
                        continue

        print("[ERROR] Failed to complete challenge after multiple attempts")
        return False

    def _check_login_errors(self) -> bool:
        """Check for login error messages."""
        error_selectors = [
            ".form__label--error",
            ".alert",
            "[data-js-module-id='guest-input-validation']",
            ".msg--error",
        ]

        for selector in error_selectors:
            try:
                error_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if error_element.is_displayed():
                    return True
            except NoSuchElementException:
                continue

        return False

    def _verify_feed_access(self) -> bool:
        """Verify that user has access to LinkedIn feed."""
        current_url = self.driver.current_url.lower()

        if "login" in current_url or "signin" in current_url:
            return False

        if "challenge" in current_url:
            return False

        page_source = self.driver.page_source.lower()

        challenge_indicators = [
            "challenge",
            "verification",
            "captcha",
            "security-challenge",
            "checkpoint",
            "two-step",
            "verify your identity",
        ]

        if any(indicator in page_source for indicator in challenge_indicators):
            return False

        auth_indicators = [
            "global-nav__me",
            "messaging",
            "notifications",
            "start a post",
            "global navigation",
            "feed",
        ]

        return any(indicator in page_source for indicator in auth_indicators)

    def _handle_welcome_page(self) -> bool:
        """Handle welcome back page with profile selection."""
        try:
            page_source = self.driver.page_source.lower()

            welcome_indicators = [
                "welcome back",
                "choose your account",
                "select account",
                "which account",
                "continue as",
            ]

            if not any(indicator in page_source for indicator in welcome_indicators):
                return True

            profile_selectors = [
                "button[data-test-id='profile-selector']",
                ".profile-selector button",
                ".account-selector button",
                "button[aria-label*='profile']",
                ".profile-card button",
                "//button[contains(text(), 'Continue')]",
                "//button[contains(text(), 'Select')]",
            ]

            for selector in profile_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if elements:
                        first_button = elements[0]
                        if first_button.is_displayed() and first_button.is_enabled():
                            self.human_behavior.click(first_button)
                            self.human_behavior.delay(1, 2)
                            return True
                except Exception:
                    continue

            return True

        except Exception:
            return True
