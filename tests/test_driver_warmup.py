"""Tests for browser warm-up functionality."""
from unittest.mock import MagicMock

from linkedin_spider.core.config import ScraperConfig
from linkedin_spider.core.driver import DriverManager


class TestBrowserWarmup:
    """Tests for the warm_up_browser method."""

    def setup_method(self) -> None:
        self.config = ScraperConfig()
        self.dm = DriverManager(self.config)
        self.dm.driver = MagicMock()

    def test_warm_up_visits_benign_sites(self) -> None:
        """Warm-up should visit Google and Wikipedia before LinkedIn."""
        self.dm.warm_up_browser()
        get_calls = self.dm.driver.get.call_args_list
        urls = [c.args[0] for c in get_calls]
        assert any("google.com" in u for u in urls)
        assert any("wikipedia.org" in u for u in urls)

    def test_warm_up_handles_navigation_errors(self) -> None:
        """Warm-up should not raise if a site fails to load."""
        self.dm.driver.get.side_effect = Exception("Navigation failed")
        self.dm.warm_up_browser()

    def test_warm_up_with_no_driver_is_noop(self) -> None:
        """Warm-up should do nothing if driver is not initialized."""
        self.dm.driver = None
        self.dm.warm_up_browser()
