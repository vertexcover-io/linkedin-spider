"""Tests for session cookie validation."""

from unittest.mock import MagicMock

from linkedin_spider.core.auth import AuthManager
from linkedin_spider.core.driver import DriverManager
from linkedin_spider.utils.human_behavior import HumanBehavior


class TestCookieValidation:
    """Tests for _validate_session_cookies."""

    def setup_method(self) -> None:
        self.driver_manager = MagicMock(spec=DriverManager)
        self.driver = MagicMock()
        self.driver_manager.driver = self.driver
        self.driver_manager.wait = MagicMock()
        self.human_behavior = MagicMock(spec=HumanBehavior)
        self.auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
        )

    def test_valid_when_li_at_present(self) -> None:
        """Session is valid when li_at cookie exists."""
        self.driver.get_cookies.return_value = [
            {"name": "li_at", "value": "abc123", "domain": ".linkedin.com"},
            {"name": "JSESSIONID", "value": "sess456", "domain": ".linkedin.com"},
        ]
        assert self.auth._validate_session_cookies() is True

    def test_invalid_when_li_at_missing(self) -> None:
        """Session is invalid without li_at cookie."""
        self.driver.get_cookies.return_value = [
            {"name": "JSESSIONID", "value": "sess456", "domain": ".linkedin.com"},
            {"name": "bcookie", "value": "bc789", "domain": ".linkedin.com"},
        ]
        assert self.auth._validate_session_cookies() is False

    def test_invalid_when_no_cookies(self) -> None:
        """Session is invalid with no cookies at all."""
        self.driver.get_cookies.return_value = []
        assert self.auth._validate_session_cookies() is False

    def test_handles_driver_error(self) -> None:
        """Should return False if driver raises."""
        self.driver.get_cookies.side_effect = Exception("Driver error")
        assert self.auth._validate_session_cookies() is False
