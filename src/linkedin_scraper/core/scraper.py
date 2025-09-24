import atexit
import json
import signal
import sys
from typing import Any

from linkedin_scraper.scrapers.company import CompanyScraper
from linkedin_scraper.scrapers.connections import ConnectionScraper
from linkedin_scraper.scrapers.conversations import ConversationScraper
from linkedin_scraper.scrapers.profile import ProfileScraper
from linkedin_scraper.scrapers.search import SearchScraper
from linkedin_scraper.utils.human_behavior import HumanBehavior
from linkedin_scraper.utils.tracking import TrackingHandler
from linkedin_scraper.core.auth import AuthManager
from linkedin_scraper.core.config import ScraperConfig
from linkedin_scraper.core.driver import DriverManager


class LinkedInSpider:
    """Main LinkedIn scraper orchestrator."""

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        li_at_cookie: str | None = None,
        config: ScraperConfig | None = None,
    ):
        self.config = config or ScraperConfig()
        self.driver_manager = DriverManager(self.config)

        self.driver = None
        self.wait = None
        self.actions = None

        self.human_behavior = None
        self.tracking_handler = None
        self.auth_manager = None

        self.profile_scraper = None
        self.search_scraper = None
        self.connection_scraper = None
        self.company_scraper = None
        self.conversation_scraper = None

        self._credentials = {"email": email, "password": password, "li_at_cookie": li_at_cookie}

        self._initialize()
        self._setup_cleanup_handlers()

    def _setup_cleanup_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._cleanup_on_exit)
        signal.signal(signal.SIGTERM, self._cleanup_on_exit)
        atexit.register(self._cleanup_on_exit)

    def _cleanup_on_exit(self, signum=None, frame=None) -> None:
        try:
            import time

            import psutil

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["name"] and "chrome" in proc.info["name"].lower():
                        cmdline = proc.info["cmdline"]
                        if cmdline and isinstance(cmdline, list):
                            cmdline_str = " ".join(cmdline)
                            if "linkedin_scraper_profiles" in cmdline_str:
                                process = psutil.Process(proc.info["pid"])
                                process.terminate()
                                try:
                                    process.wait(timeout=1)
                                except psutil.TimeoutExpired:
                                    process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            time.sleep(0.2)
        except Exception:
            pass

        if signum is not None:
            sys.exit(0)

    def _initialize(self) -> None:
        """Initialize the scraper components."""
        self.driver = self.driver_manager.setup_driver()
        self.wait = self.driver_manager.wait
        self.actions = self.driver_manager.actions

        self.human_behavior = HumanBehavior(self.driver, self.wait, self.actions, self.config)
        self.tracking_handler = TrackingHandler(self.driver, self.wait, self.actions)

        self.auth_manager = AuthManager(
            self.driver_manager, self.human_behavior, **self._credentials
        )

        self._initialize_scrapers()
        self._configure_anti_detection()

        self.auth_manager.authenticate()

    def _initialize_scrapers(self) -> None:
        """Initialize all scraper modules."""
        scraper_args = (self.driver, self.wait, self.human_behavior, self.tracking_handler)

        self.profile_scraper = ProfileScraper(*scraper_args)
        self.search_scraper = SearchScraper(*scraper_args)
        self.connection_scraper = ConnectionScraper(*scraper_args)
        self.company_scraper = CompanyScraper(*scraper_args)
        self.conversation_scraper = ConversationScraper(*scraper_args)

    def _configure_anti_detection(self) -> None:
        """Configure anti-detection measures."""
        self.tracking_handler.inject_anti_detection_scripts()

    def scrape_profile(self, profile_url: str) -> dict[str, Any] | None:
        """Scrape a LinkedIn profile."""
        return self.profile_scraper.scrape_profile(profile_url)

    def search_profiles(
        self, query: str, max_results: int = 10, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        """Search for LinkedIn profiles."""
        return self.search_scraper.search_profiles(query, max_results, filters)

    def scrape_company(self, company_url: str) -> dict[str, Any] | None:
        """Scrape a LinkedIn company page."""
        return self.company_scraper.scrape_company(company_url)

    def scrape_incoming_connections(self, max_results: int = 10) -> list[dict[str, Any]]:
        """Scrape incoming connection requests."""
        return self.connection_scraper.scrape_incoming_connections(max_results)

    def scrape_outgoing_connections(self, max_results: int = 10) -> list[dict[str, Any]]:
        """Scrape outgoing connection requests."""
        return self.connection_scraper.scrape_outgoing_connections(max_results)

    def scrape_conversations_list(self, max_results: int = 10) -> list[dict[str, Any]]:
        """Scrape list of conversations."""
        return self.conversation_scraper.scrape_conversations_list(max_results)

    def scrape_conversation_messages(
        self, participant_name: str | None = None
    ) -> dict[str, Any] | None:
        """Scrape messages from a conversation."""
        return self.conversation_scraper.scrape_conversation_messages(participant_name)

    def send_connection_request(self, profile_url: str, note: str | None = None) -> bool:
        """Send a connection request to a profile."""
        return self.connection_scraper.send_connection_request(profile_url, note)

    def extract_search_data(self) -> list[dict[str, Any]]:
        """Extract anonymous data from search results."""
        return self.search_scraper.extract_anonymous_data()

    def scrape_search_results(
        self, query: str, max_results: int = 5, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        """Scrape search results with fallback to anonymous data."""
        profile_urls = self.search_profiles(query, max_results, filters)

        if not profile_urls:
            anonymous_data = self.extract_search_data()
            if anonymous_data:
                return anonymous_data
            return []

        profiles_data = []

        for i, profile_info in enumerate(profile_urls, 1):
            if i > 1:
                self.human_behavior.delay(2, 5)

            profile_url = profile_info.get("profile_url")
            if self._is_valid_profile_url(profile_url):
                profile_data = self.scrape_profile(profile_url)
                if profile_data:
                    profiles_data.append(profile_data)
            else:
                limited_data = self._create_limited_profile_data(profile_info)
                if limited_data:
                    profiles_data.append(limited_data)

            if i < len(profile_urls):
                self.tracking_handler.simulate_natural_browsing()

        return profiles_data

    def save_to_json(self, data: Any, filename: str) -> None:
        """Save data to JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def keep_alive(self) -> bool:
        """Check if session is still alive."""
        try:
            self.driver.execute_script("return window.location.href;")
            return True
        except Exception:
            return False

    def clear_saved_session(self) -> bool:
        """Clear saved session data."""
        return self.driver_manager.clear_saved_cookies()

    def close(self) -> None:
        """Close the scraper and clean up resources."""
        if self.driver_manager:
            self.human_behavior.delay(1, 2)
            self.driver_manager.close()
        self._cleanup_on_exit()

    def _is_valid_profile_url(self, profile_url: str | None) -> bool:
        """Check if profile URL is valid."""
        return (
            profile_url
            and profile_url != "N/A"
            and isinstance(profile_url, str)
            and "linkedin.com/in/" in profile_url
        )

    def _create_limited_profile_data(self, profile_info: dict) -> dict[str, Any] | None:
        """Create limited profile data from search results."""
        if profile_info.get("name") == "N/A" and profile_info.get("headline") == "N/A":
            return None

        return {
            "name": profile_info.get("name", "N/A"),
            "headline": profile_info.get("headline", "N/A"),
            "location": profile_info.get("location", "N/A"),
            "profile_url": "N/A",
            "about": "N/A",
            "experience": [],
        }
