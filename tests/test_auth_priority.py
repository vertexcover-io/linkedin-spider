"""Tests for authentication priority order."""

import inspect
from unittest.mock import MagicMock

import pytest

from linkedin_spider.core.auth import AuthManager
from linkedin_spider.core.driver import DriverManager
from linkedin_spider.utils.human_behavior import HumanBehavior


class TestAuthPriority:
    """Tests for the authenticate method's priority order."""

    def setup_method(self) -> None:
        self.driver_manager = MagicMock(spec=DriverManager)
        self.driver = MagicMock()
        self.driver_manager.driver = self.driver
        self.wait = MagicMock()
        self.driver_manager.wait = self.wait
        self.human_behavior = MagicMock(spec=HumanBehavior)

    def test_saved_cookies_tried_first(self) -> None:
        """Saved cookies should be the first auth method attempted."""
        auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
        )
        auth._try_saved_cookies = MagicMock(return_value=True)
        auth._authenticate_with_cookie = MagicMock()
        auth._manual_login = MagicMock()

        result = auth.authenticate()

        assert result is True
        auth._try_saved_cookies.assert_called_once()
        auth._authenticate_with_cookie.assert_not_called()
        auth._manual_login.assert_not_called()

    def test_li_at_cookie_tried_second(self) -> None:
        """li_at cookie should be tried after saved cookies fail."""
        auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
            li_at_cookie="test_cookie_value",
        )
        auth._try_saved_cookies = MagicMock(return_value=False)
        auth._authenticate_with_cookie = MagicMock(return_value=True)
        auth._manual_login = MagicMock()

        result = auth.authenticate()

        assert result is True
        auth._try_saved_cookies.assert_called_once()
        auth._authenticate_with_cookie.assert_called_once_with("test_cookie_value")
        auth._manual_login.assert_not_called()

    def test_manual_login_tried_third_when_not_headless(self) -> None:
        """Manual login should be tried when cookies fail and browser is not headless."""
        self.driver_manager.config = MagicMock()
        self.driver_manager.config.headless = False

        auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
        )
        auth._try_saved_cookies = MagicMock(return_value=False)
        auth._manual_login = MagicMock(return_value=True)

        result = auth.authenticate()

        assert result is True
        auth._manual_login.assert_called_once()

    def test_manual_login_skipped_in_headless(self) -> None:
        """Manual login should be skipped in headless mode."""
        self.driver_manager.config = MagicMock()
        self.driver_manager.config.headless = True

        auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
        )
        auth._try_saved_cookies = MagicMock(return_value=False)
        auth._manual_login = MagicMock()

        with pytest.raises(Exception, match="Authentication failed"):
            auth.authenticate()

        auth._manual_login.assert_not_called()

    def test_error_raised_when_all_methods_fail(self) -> None:
        """Exception should be raised when all auth methods fail."""
        self.driver_manager.config = MagicMock()
        self.driver_manager.config.headless = False

        auth = AuthManager(
            driver_manager=self.driver_manager,
            human_behavior=self.human_behavior,
        )
        auth._try_saved_cookies = MagicMock(return_value=False)
        auth._manual_login = MagicMock(return_value=False)

        with pytest.raises(Exception, match="Authentication failed"):
            auth.authenticate()

    def test_constructor_no_longer_accepts_email_password(self) -> None:
        """AuthManager constructor should not accept email/password."""
        sig = inspect.signature(AuthManager.__init__)
        params = list(sig.parameters.keys())
        assert "email" not in params
        assert "password" not in params
