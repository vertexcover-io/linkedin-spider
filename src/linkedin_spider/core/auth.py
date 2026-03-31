import logging

from selenium.webdriver.common.by import By

from linkedin_spider.core.driver import DriverManager
from linkedin_spider.utils.human_behavior import HumanBehavior

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles LinkedIn authentication via saved cookies, li_at cookie, or manual browser login."""

    def __init__(
        self,
        driver_manager: DriverManager,
        human_behavior: HumanBehavior,
        li_at_cookie: str | None = None,
    ):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver
        self.wait = driver_manager.wait
        self.human_behavior = human_behavior
        self.li_at_cookie = li_at_cookie

    def authenticate(self) -> bool:
        """
        Authenticate using available methods with smart fallback priority.

        Priority order:
        1. Try saved cookies from profile directory (no user interaction)
        2. Try li_at cookie parameter (if provided)
        3. Open browser for manual login (if not headless)
        4. Raise error if all methods fail

        Returns:
            bool: True if authentication succeeded

        Raises:
            Exception: If all authentication methods fail
        """
        # Priority 1: Check saved cookies first (fastest, no interaction)
        logger.info("Checking for saved cookies in profile directory...")
        if self._try_saved_cookies():
            logger.info("Successfully authenticated using saved cookies")
            return True
        logger.info("No valid saved cookies found")

        # Priority 2: Try li_at cookie if provided
        if self.li_at_cookie:
            logger.info("Trying li_at cookie from parameter...")
            if self._authenticate_with_cookie(self.li_at_cookie):
                self.driver_manager.save_cookies()
                return True
            logger.warning("Provided li_at cookie is invalid or expired")

        # Priority 3: Manual browser login (only if not headless)
        if not self.driver_manager.config.headless:
            logger.info("Starting manual browser login...")
            self.driver_manager.warm_up_browser()
            if self._manual_login():
                self.driver_manager.save_cookies()
                return True
            logger.warning("Manual login failed or timed out")

        # All methods exhausted
        raise Exception(  # noqa: TRY002
            "Authentication failed. All methods exhausted.\n"
            "Options:\n"
            "  1. Run with --login flag to open browser for manual login\n"
            "  2. Provide li_at cookie via --cookie parameter or LINKEDIN_COOKIE env var\n"
            "  3. Ensure headless mode is off for manual login"
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
                return self._quick_feed_check() and self._validate_session_cookies()

            self.driver.get("https://www.linkedin.com")
            self.human_behavior.delay(1, 2)
            current_url = self.driver.current_url.lower()

            return (
                "login" not in current_url
                and "signin" not in current_url
                and self._quick_feed_check()
                and self._validate_session_cookies()
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

    def _validate_session_cookies(self) -> bool:
        """Validate that essential LinkedIn session cookies are present."""
        try:
            cookies = self.driver.get_cookies()
            cookie_names = {c["name"] for c in cookies}

            if "li_at" not in cookie_names:
                logger.warning("Missing essential cookie: li_at")
                return False

            return True
        except Exception:
            logger.debug("Failed to validate session cookies")
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
        except Exception:
            logger.exception("Cookie authentication exception")
            return False
        else:
            if success:
                self.human_behavior.delay(1, 2)
                self._handle_welcome_page()
                return self._is_authenticated()

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

    def _manual_login(self, timeout: int = 300) -> bool:
        """
        Open LinkedIn login page and wait for the user to complete login manually.

        This handles 2FA, captcha, and any other challenges transparently since
        the user completes them in the real browser window.

        Args:
            timeout: Maximum seconds to wait for login completion (default: 5 minutes)

        Returns:
            bool: True if user successfully logged in within the timeout
        """
        import time as _time

        try:
            logger.info(
                "Opening LinkedIn login page. Please log in manually in the browser window. "
                "You have %d seconds to complete login (including 2FA/captcha).",
                timeout,
            )
            self.driver.get("https://www.linkedin.com/login")
            self.human_behavior.delay(2, 3)

            start = _time.monotonic()
            poll_interval = 2

            while (_time.monotonic() - start) < timeout:
                try:
                    current_url = self.driver.current_url.lower()

                    # Still on login/challenge page — keep waiting
                    if any(
                        indicator in current_url
                        for indicator in [
                            "login",
                            "signin",
                            "challenge",
                            "checkpoint",
                            "verification",
                        ]
                    ):
                        _time.sleep(poll_interval)
                        continue

                    # Might be authenticated — verify with feed check
                    if self._is_authenticated():
                        logger.info("Manual login successful!")
                        return True

                    # URL changed but not clearly authenticated — keep polling
                    _time.sleep(poll_interval)

                except Exception:
                    logger.debug("Error during login poll, retrying...")
                    _time.sleep(poll_interval)

            logger.warning("Manual login timed out after %d seconds", timeout)
            return False

        except Exception:
            logger.exception("Manual login failed with error")
            return False

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
                except Exception:  # noqa: S112
                    continue
        except Exception:
            return True
        else:
            return True
