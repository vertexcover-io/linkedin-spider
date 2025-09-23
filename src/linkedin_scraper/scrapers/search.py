import urllib.parse
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_scraper.scrapers.base import BaseScraper
from linkedin_scraper.scrapers.search_filters import SearchFilterHandler


class SearchScraper(BaseScraper):
    """Scraper for LinkedIn search functionality."""

    def __init__(self, driver: Any, wait: Any, human_behavior: Any, tracking_handler: Any) -> None:
        super().__init__(driver, wait, human_behavior, tracking_handler)
        self.filter_handler = SearchFilterHandler(driver, wait, human_behavior)

    def _find_element_in_parent(self, parent: WebElement, by: By, value: str) -> WebElement | None:
        """Find element within parent element."""
        try:
            return parent.find_element(by, value)
        except Exception:
            return None

    def _find_elements_safe(self, by: By, value: str, timeout: int = 5) -> list[WebElement]:
        """Safely find elements with timeout."""
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            return self.driver.find_elements(by, value)
        except TimeoutException:
            return []

    def _extract_text_safe(self, element: WebElement) -> str:
        """Safely get element text."""
        try:
            return element.text.strip()
        except Exception:
            return ""

    def _extract_attribute_safe(self, element: WebElement, attribute: str) -> str:
        """Safely get element attribute."""
        try:
            value = element.get_attribute(attribute)
            return value.strip() if value else ""
        except Exception:
            return ""

    def _scroll_and_wait(self, pixels: int = 300) -> None:
        """Scroll and wait with human behavior."""
        try:
            self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            self.human_behavior.delay(0.5, 1.5)
        except Exception:
            pass

    def search_profiles(
        self, query: str, max_results: int = 10, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        """Search for LinkedIn profiles."""
        return self.scrape(query, max_results, filters)

    def extract_anonymous_data(self) -> list[dict[str, Any]]:
        """Extract anonymous data from current search results."""
        try:
            results = []
            containers = self._find_elements_safe(
                By.CSS_SELECTOR, "div[data-view-name='people-search-result']"
            )

            for container in containers[:10]:
                try:
                    name_elem = self._find_element_in_parent(
                        container, By.CSS_SELECTOR, 'a[data-view-name="search-result-lockup-title"]'
                    )
                    name = self._extract_text_safe(name_elem) if name_elem else "Anonymous"

                    headline_elements = container.find_elements(By.CSS_SELECTOR, "p")
                    headline = (
                        headline_elements[1].text.strip() if len(headline_elements) > 1 else "N/A"
                    )

                    location = (
                        headline_elements[2].text.strip() if len(headline_elements) > 2 else "N/A"
                    )

                    result = {
                        "name": name,
                        "headline": headline,
                        "location": location,
                        "profile_url": "N/A",
                        "about": "N/A",
                        "experience": [],
                    }

                    if result["name"] != "Anonymous" or result["headline"] != "N/A":
                        results.append(result)

                except Exception:
                    continue

            return results
        except Exception:
            return []

    def search_and_apply_filters(
        self,
        query: str,
        location: str | None = None,
        industry: str | None = None,
        current_company: str | None = None,
        connections: str | None = None,
        connection_of: str | None = None,
        followers_of: str | None = None,
    ) -> Any:
        return self.filter_handler.search_and_apply_filters(
            query=query,
            location=location,
            industry=industry,
            current_company=current_company,
            connections=connections,
            connection_of=connection_of,
            followers_of=followers_of,
        )

    def scrape(
        self, query: str, max_results: int = 10, filters: dict | None = None
    ) -> list[dict[str, Any]]:
        """Main search implementation."""
        if filters:
            self.search_and_apply_filters(
                query=query,
                location=filters.get("location"),
                industry=filters.get("industry"),
                current_company=filters.get("current_company"),
                connections=filters.get("connections"),
                connection_of=filters.get("connection_of"),
                followers_of=filters.get("followers_of"),
            )
        else:
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"
            if not self.navigate_to_url(search_url):
                self.log_action("ERROR", f"Failed to navigate to search: {query}")
                return []

        self.log_action("INFO", f"Searching for: {query}")

        try:
            self.human_behavior.delay(1.0, 3.0)

            results = []
            containers = self._find_elements_safe(
                By.CSS_SELECTOR, "div[data-view-name='people-search-result']"
            )

            for i, container in enumerate(containers[:max_results]):
                try:
                    name_elem = self._find_element_in_parent(
                        container, By.CSS_SELECTOR, 'a[data-view-name="search-result-lockup-title"]'
                    )
                    if name_elem:
                        name = self._extract_text_safe(name_elem)
                        href = self._extract_attribute_safe(name_elem, "href")
                        profile_url = href if href and "linkedin.com/in/" in href else "N/A"
                    else:
                        name = "N/A"
                        profile_url = "N/A"

                    headline_elements = container.find_elements(By.CSS_SELECTOR, "p")
                    headline = (
                        headline_elements[1].text.strip() if len(headline_elements) > 1 else "N/A"
                    )
                    location = (
                        headline_elements[2].text.strip() if len(headline_elements) > 2 else "N/A"
                    )

                    try:
                        img_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, "img")
                        image_url = (
                            self._extract_attribute_safe(img_elem, "src") if img_elem else "N/A"
                        )
                    except:
                        image_url = "N/A"

                    result = {
                        "name": name,
                        "headline": headline,
                        "location": location,
                        "profile_url": profile_url,
                        "image_url": image_url,
                    }
                    is_duplicate = False
                    for existing_result in results:
                        if (
                            existing_result.get("profile_url") == result.get("profile_url")
                            and result.get("profile_url") != "N/A"
                        ) or (
                            existing_result.get("name") == result.get("name")
                            and result.get("name") != "N/A"
                        ):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        results.append(result)

                    if (i + 1) % 3 == 0:
                        self._scroll_and_wait(300)

                except Exception:
                    continue

            self.log_action("SUCCESS", f"Found {len(results)} profiles for query: {query}")
            return results

        except Exception as e:
            self.log_action("ERROR", f"Search failed: {e!s}")
            return []

    def get_applied_filters(self) -> Any:
        return self.filter_handler.get_applied_filters()

    def reset_filters(self) -> Any:
        return self.filter_handler.reset_filters()
