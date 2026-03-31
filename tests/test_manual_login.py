"""Tests for manual login flow."""

from unittest.mock import MagicMock, PropertyMock

from linkedin_spider.core.auth import AuthManager
from linkedin_spider.core.driver import DriverManager
from linkedin_spider.utils.human_behavior import HumanBehavior


class TestManualLogin:
    """Tests for the _manual_login method."""

    def setup_method(self) -> None:
        self.driver_manager = MagicMock(spec=DriverManager)
        self.driver = MagicMock()
        self.driver_manager.driver = self.driver
        self.wait = MagicMock()
        self.driver_manager.wait = self.wait
        self.human_behavior = MagicMock(spec=HumanBehavior)
        self.auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
        )

    def test_manual_login_navigates_to_login_page(self) -> None:
        """Manual login should navigate to LinkedIn login page."""
        self.driver.current_url = "https://www.linkedin.com/feed/"
        self.driver.page_source = "<html>global-nav__me messaging</html>"
        self.driver.get_cookies.return_value = [
            {"name": "li_at", "value": "abc123", "domain": ".linkedin.com"},
        ]

        result = self.auth._manual_login(timeout=5)
        assert result is True

        get_calls = [c.args[0] for c in self.driver.get.call_args_list]
        assert any("linkedin.com/login" in url for url in get_calls)

    def test_manual_login_times_out(self) -> None:
        """Manual login should return False after timeout."""
        self.driver.current_url = "https://www.linkedin.com/login"
        self.driver.page_source = "<html>login form</html>"

        result = self.auth._manual_login(timeout=2)
        assert result is False

    def test_manual_login_detects_feed_access(self) -> None:
        """Manual login should detect successful auth via feed indicators."""
        call_count = 0

        def mock_current_url() -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return "https://www.linkedin.com/login"
            return "https://www.linkedin.com/feed/"

        type(self.driver).current_url = PropertyMock(side_effect=mock_current_url)
        self.driver.page_source = "<html>global-nav__me notifications</html>"
        self.driver.get_cookies.return_value = [
            {"name": "li_at", "value": "abc123", "domain": ".linkedin.com"},
        ]

        result = self.auth._manual_login(timeout=10)
        assert result is True
