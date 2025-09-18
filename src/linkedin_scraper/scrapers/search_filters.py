import re
import urllib.parse
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class SearchFilterHandler:
    def __init__(self, driver: Any, wait: Any, human_behavior: Any) -> None:
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.current_filters = {}

    def search_and_apply_filters(
        self,
        query: str,
        location: str | None = None,
        industry: str | None = None,
        current_company: str | None = None,
        connections: str | None = None,
        connection_of: str | None = None,
        followers_of: str | None = None,
    ) -> str:
        base_search_url = (
            f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"
        )
        self.driver.get(base_search_url)

        self.human_behavior.delay(2, 4)
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")
            )
        )

        applied_filters = {}

        if location:
            location_filter = self._apply_location_filter(location)
            if location_filter:
                applied_filters["location"] = location_filter
                self._click_show_results()

        if industry:
            industry_filter = self._apply_industry_filter(industry)
            if industry_filter:
                applied_filters["industry"] = industry_filter
                self._click_show_results()

        if current_company:
            company_filter = self._apply_company_filter(current_company)
            if company_filter:
                applied_filters["current_company"] = company_filter
                self._click_show_results()

        if connections:
            connection_filter = self._apply_connection_filter(connections)
            if connection_filter:
                applied_filters["connections"] = connection_filter

        self.current_filters = applied_filters
        return self.driver.current_url

    def _apply_location_filter(self, location_query: str) -> dict[str, Any] | None:
        try:
            location_button = self._find_filter_button_by_text("Location")

            if location_button:
                self.driver.execute_script("arguments[0].click();", location_button)
                self.human_behavior.delay(1, 2)

                dropdown_opened = self._wait_for_dropdown()
                if dropdown_opened:
                    return self._search_and_select_filter_option(location_query, "location")

            return None
        except Exception as e:
            print(f"Error applying location filter: {e!s}")
            return None

    def _apply_industry_filter(self, industry_query: str) -> dict[str, Any] | None:
        try:
            all_filters_btn = self._find_button_by_text("All filters")
            if all_filters_btn:
                self.driver.execute_script("arguments[0].click();", all_filters_btn)
                self.human_behavior.delay(1, 3)

                industry_section = self._find_filter_modal_section("Industry")
                if industry_section:
                    return self._search_in_modal_section(
                        industry_section, industry_query, "industry"
                    )

            return None
        except Exception as e:
            print(f"Error applying industry filter: {e!s}")
            return None

    def _apply_company_filter(self, company_query: str) -> dict[str, Any] | None:
        try:
            company_button = self._find_filter_button_by_text("Current companies")
            if company_button:
                self.driver.execute_script("arguments[0].click();", company_button)
                self.human_behavior.delay(1, 2)

                dropdown_opened = self._wait_for_dropdown()
                if dropdown_opened:
                    return self._search_and_select_filter_option(company_query, "company")

            return None
        except Exception as e:
            print(f"Error applying company filter: {e!s}")
            return None

    def _apply_connection_filter(self, connection_level: str) -> dict[str, Any] | None:
        try:
            connection_mapping = {
                "1st": "1st",
                "first": "1st",
                "1": "1st",
                "2nd": "2nd",
                "second": "2nd",
                "2": "2nd",
                "3rd": "3rd+",
                "third": "3rd+",
                "3": "3rd+",
            }

            target_connection = connection_mapping.get(connection_level.lower())
            if not target_connection:
                return None

            connection_button = self._find_filter_button_by_text(target_connection)
            if connection_button:
                self.driver.execute_script("arguments[0].click();", connection_button)
                self.human_behavior.delay(1, 2)
                return {"level": target_connection, "param": self._extract_connection_param()}

            return None
        except Exception as e:
            print(f"Error applying connection filter: {e!s}")
            return None

    def _find_filter_button_by_text(self, text: str) -> WebElement | None:
        try:
            buttons = self.driver.find_elements(
                By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']"
            )
            for button in buttons:
                if text.lower() in button.text.lower():
                    return button
            return None
        except:
            return None

    def _find_button_by_text(self, text: str) -> WebElement | None:
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if text.lower() in button.text.lower():
                    return button
            return None
        except:
            return None

    def _wait_for_dropdown(self, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[placeholder*='Add'], input[type='text']")
                )
            )
            return True
        except TimeoutException:
            return False

    def _search_and_select_filter_option(
        self, query: str, filter_type: str
    ) -> dict[str, Any] | None:
        try:
            search_input = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-menu-tyah']")
                )
            )
            search_input.clear()
            search_input.send_keys(query)
            self.human_behavior.delay(1, 2)

            suggestions = self._wait_for_suggestions()
            if suggestions:
                best_match_text = None
                best_match_found = False

                for suggestion in suggestions:
                    try:
                        text_element = suggestion.find_element(By.CSS_SELECTOR, "p")
                        suggestion_text = text_element.text.strip()

                        if query.lower() in suggestion_text.lower():
                            best_match_text = suggestion_text
                            self.driver.execute_script("arguments[0].click();", suggestion)
                            best_match_found = True
                            break
                    except Exception:
                        continue

                if best_match_found:
                    self.human_behavior.delay(1, 2)
                    return {
                        "query": query,
                        "selected": best_match_text,
                        "param": self._extract_filter_param(filter_type),
                    }

            return None
        except Exception as e:
            print(f"Error in search and select: {e!s}")
            return None

    def _wait_for_suggestions(self, timeout: int = 5) -> list[WebElement]:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "[data-view-name='search-filter-top-bar-menu-item'], [role='checkbox'], [role='option']",
                    )
                )
            )
            return self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-view-name='search-filter-top-bar-menu-item'], [role='checkbox'], [role='option']",
            )
        except TimeoutException:
            return []

    def _find_best_match(self, suggestions: list[WebElement], query: str) -> WebElement | None:
        query_lower = query.lower()
        best_match = None
        highest_score = 0

        for suggestion in suggestions:
            try:
                text_element = (
                    suggestion.find_element(By.TAG_NAME, "p")
                    if suggestion.find_elements(By.TAG_NAME, "p")
                    else suggestion
                )
                text = text_element.text.lower()
                if query_lower in text:
                    score = len(query_lower) / len(text) if text else 0
                    if score > highest_score:
                        highest_score = score
                        best_match = suggestion
            except:
                continue

        return best_match if best_match else (suggestions[0] if suggestions else None)

    def _find_filter_modal_section(self, section_name: str) -> WebElement | None:
        try:
            headings = self.driver.find_elements(
                By.CSS_SELECTOR, "h3, h2, legend, .filter-section-title"
            )
            for heading in headings:
                if section_name.lower() in heading.text.lower():
                    return heading.find_element(By.XPATH, "./following-sibling::*[1]")
            return None
        except:
            return None

    def _search_in_modal_section(
        self, section: WebElement, query: str, filter_type: str
    ) -> dict[str, Any] | None:
        try:
            search_input = section.find_element(By.CSS_SELECTOR, "input[type='text']")
            search_input.clear()
            search_input.send_keys(query)
            self.human_behavior.delay(1, 2)

            options = section.find_elements(By.CSS_SELECTOR, "[role='checkbox'], .option-item")
            best_match = self._find_best_match(options, query)

            if best_match:
                self.driver.execute_script("arguments[0].click();", best_match)
                self.human_behavior.delay(1, 2)

                apply_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button[data-control-name='all_filters_apply']"
                )
                if apply_btn:
                    self.driver.execute_script("arguments[0].click();", apply_btn)
                    self.human_behavior.delay(2, 3)
                    self.wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")
                        )
                    )

                return {
                    "query": query,
                    "selected": best_match.text,
                    "param": self._extract_filter_param(filter_type),
                }

            return None
        except Exception as e:
            print(f"Error in modal section search: {e!s}")
            return None

    def _extract_filter_param(self, filter_type: str) -> dict[str, str]:
        current_url = self.driver.current_url
        parsed_url = urllib.parse.urlparse(current_url)
        params = urllib.parse.parse_qs(parsed_url.query)

        param_map = {
            "location": ["geoUrn", "location"],
            "industry": ["industryUrn", "industry"],
            "company": ["currentCompany", "companyUrn"],
            "connections": ["network", "connectionDepth"],
        }

        for param_key in param_map.get(filter_type, []):
            if param_key in params:
                return {param_key: params[param_key][0]}

        return {}

    def _extract_connection_param(self) -> dict[str, str]:
        current_url = self.driver.current_url
        if "network=" in current_url:
            network_match = re.search(r"network=([^&]+)", current_url)
            if network_match:
                return {"network": network_match.group(1)}
        return {}

    def get_applied_filters(self) -> dict[str, Any]:
        return self.current_filters

    def _click_show_results(self) -> bool:
        try:
            selectors = [
                "[data-view-name='search-filter-top-bar-menu-submit']",
                "button[componentkey*='submit']",
                "button:contains('Show results')",
                "button[type='button']:last-child",
            ]

            for selector in selectors:
                try:
                    if "contains" in selector:
                        show_results_btn = self.driver.execute_script(
                            "return Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Show results'));"
                        )
                    else:
                        show_results_btn = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )

                    if show_results_btn:
                        self.driver.execute_script("arguments[0].click();", show_results_btn)
                        self.human_behavior.delay(2, 4)
                        self.wait.until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")
                            )
                        )
                        return True
                except:
                    continue

            return False
        except Exception as e:
            print(f"Error clicking show results: {e!s}")
            return False

    def reset_filters(self) -> bool:
        try:
            reset_btn = self._find_button_by_text("Reset")
            if reset_btn:
                self.driver.execute_script("arguments[0].click();", reset_btn)
                self.human_behavior.delay(1, 2)
                self.current_filters = {}
                return True
            return False
        except:
            return False
