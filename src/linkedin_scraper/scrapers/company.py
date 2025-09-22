import re
from typing import Any

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from linkedin_scraper.utils.pattern_detector import PatternDetector
from linkedin_scraper.scrapers.base import BaseScraper


class CompanyScraper(BaseScraper):
    """Scraper for LinkedIn company pages."""

    def __init__(self, driver: Any, wait: Any, human_behavior: Any, tracking_handler: Any) -> None:
        super().__init__(driver, wait, human_behavior, tracking_handler)
        self.pattern_detector = PatternDetector()

    def _is_valid_company_url(self, url: str) -> bool:
        if not url or not isinstance(url, str) or url == "N/A":
            return False
        company_pattern = r"^https?://(www\.)?linkedin\.com/company/"
        return bool(re.match(company_pattern, url))

    def scrape_company(self, company_url: str) -> dict[str, Any] | None:
        """Scrape a LinkedIn company page."""
        return self.scrape(company_url)

    def scrape(self, company_url: str) -> dict[str, Any] | None:
        """Main company scraping implementation."""
        if not self._is_valid_company_url(company_url):
            self.log_action("ERROR", f"Invalid company URL: {company_url}")
            return None

        self.log_action("INFO", f"Scraping company: {company_url}")

        try:
            self.driver.get(company_url)

            if not self._wait_for_company_page():
                self.log_action("ERROR", f"Failed to load company page: {company_url}")
                return None

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_behavior.delay(1, 2)

            company_data = {}
            company_data["name"] = self._extract_company_name()
            company_data["tagline"] = self._extract_tagline()
            company_data["logo_url"] = self._extract_logo()
            company_data["is_verified"] = self._extract_verification_status()
            company_data["industry"] = self._extract_industry()
            company_data["location"] = self._extract_location()
            company_data["followers"] = self._extract_followers()
            company_data["employee_count"] = self._extract_employee_count()
            company_data["company_url"] = company_url

            about_data = self._navigate_to_about_page()
            if about_data:
                company_data.update(about_data)

            self.human_behavior.delay(1, 2)

            self.log_action(
                "SUCCESS", f"Successfully scraped company: {company_data.get('name', 'Unknown')}"
            )

            return company_data

        except Exception as e:
            self.log_action("ERROR", f"Error scraping company {company_url}: {e!s}")
            return None

    def _extract_company_name(self) -> str:
        try:
            selectors = [
                "h1.org-top-card-summary__title",
                "h1[class*='org-top-card-summary__title']",
                ".org-top-card-primary-content h1",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = element.text.strip()
                    if name and len(name) > 1:
                        return name
                except NoSuchElementException:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_tagline(self) -> str:
        try:
            selectors = [
                ".org-top-card-summary__tagline",
                "p[class*='org-top-card-summary__tagline']",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    tagline = element.text.strip()
                    if tagline:
                        return tagline
                except NoSuchElementException:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_logo(self) -> str:
        try:
            selectors = [
                ".org-top-card-primary-content__logo",
                "img[class*='org-top-card-primary-content__logo']",
                ".org-top-card-primary-content__logo-container img",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logo_url = element.get_attribute("src")
                    if logo_url:
                        return logo_url
                except NoSuchElementException:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_verification_status(self) -> bool:
        try:
            verified_selectors = [
                "svg[data-test-icon='verified-medium']",
                "[aria-label='Verified']",
                ".org-top-card-summary__badge",
            ]

            for selector in verified_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        return True
                except NoSuchElementException:
                    continue

            return False
        except Exception:
            return False

    def _extract_industry(self) -> str:
        try:
            selectors = [
                ".org-top-card-summary-info-list__info-item",
                "[class*='org-top-card-summary-info-list__info-item']",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and (
                            "Technology" in text
                            or "Information" in text
                            or "Internet" in text
                            or "Software" in text
                            or "Finance" in text
                            or "Healthcare" in text
                            or "Manufacturing" in text
                            or "Education" in text
                            or "Retail" in text
                            or "Services" in text
                        ):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_location(self) -> str:
        try:
            selectors = [
                ".org-top-card-summary-info-list__info-item",
                "[class*='org-top-card-summary-info-list__info-item']",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and self.pattern_detector.is_likely_location(text):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_followers(self) -> str:
        try:
            selectors = [
                ".org-top-card-summary-info-list__info-item",
                "[class*='org-top-card-summary-info-list__info-item']",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and ("followers" in text.lower() or "M" in text or "K" in text):
                            if (
                                "followers" in text.lower()
                                or any(char in text for char in ["M", "K"])
                                and len(text) < 10
                            ):
                                return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_employee_count(self) -> str:
        try:
            selectors = [
                "a[class*='org-top-card-summary-info-list__info-item-link']",
                ".org-top-card-summary-info-list__info-item-link",
                ".org-top-card-summary-info-list__info-item",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and (
                            "employee" in text.lower() or self._contains_employee_range(text)
                        ):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _contains_employee_range(self, text: str) -> bool:
        patterns = [
            r"\d+[-–]\d+",
            r"\d+K[-–]\d+K",
            r"\d+,\d+[-–]\d+,\d+",
            r"\d+\+",
            r"\d+K\+",
            r"\d+,\d+\+",
            r"[1-9]\d*\s*employees?",
            r"[1-9]\d*K\s*employees?",
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _navigate_to_about_page(self) -> dict[str, str]:
        try:
            current_url = self.driver.current_url
            if "/about/" not in current_url:
                about_url = current_url.rstrip("/") + "/about/"
                self.driver.get(about_url)
                self.human_behavior.delay(2, 3)

            if not self._wait_for_about_page():
                return {}

            about_data = {}
            about_data["description"] = self._extract_description()
            about_data["website"] = self._extract_website()
            about_data["headquarters"] = self._extract_headquarters()
            about_data["founded"] = self._extract_founded()
            about_data["company_size"] = self._extract_company_size()
            about_data["associated_members"] = self._extract_associated_members()
            about_data["verified_date"] = self._extract_verified_date()

            return about_data

        except Exception as e:
            self.log_action("ERROR", f"Error navigating to about page: {e!s}")
            return {}

    def _extract_description(self) -> str:
        try:
            selectors = [
                ".break-words.white-space-pre-wrap.t-black--light.text-body-medium",
                "p[class*='break-words white-space-pre-wrap']",
                ".org-about-module p",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description = element.text.strip()
                    if description and len(description) > 20:
                        return description
                except NoSuchElementException:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_website(self) -> str:
        try:
            selectors = [
                "a[class*='link-without-visited-state'] span[dir='ltr']",
                "dd.mb4 a span[dir='ltr']",
                "a[href*='http'] span[dir='ltr']",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    website = element.text.strip()
                    if website and ("http" in website or "." in website):
                        return website
                except NoSuchElementException:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_headquarters(self) -> str:
        try:
            selectors_strategies = [
                ("dt h3", "headquarters"),
                (".text-heading-medium", "headquarters"),
                ("h3.text-heading-medium", "headquarters"),
            ]

            for selector, keyword in selectors_strategies:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if keyword in element.text.lower():
                            try:
                                dd_element = element.find_element(
                                    By.XPATH, "./../../following-sibling::dd"
                                )
                                headquarters = dd_element.text.strip()
                                if headquarters:
                                    return headquarters
                            except:
                                try:
                                    parent = element.find_element(By.XPATH, "./../..")
                                    dd_element = parent.find_element(
                                        By.XPATH, "./following-sibling::dd"
                                    )
                                    headquarters = dd_element.text.strip()
                                    if headquarters:
                                        return headquarters
                                except:
                                    continue
                except Exception:
                    continue

            fallback_selectors = [
                "dd.mb4.t-black--light.text-body-medium",
                ".t-black--light.text-body-medium",
            ]

            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if (
                            text
                            and self.pattern_detector.is_likely_location(text)
                            and len(text) > 5
                        ):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_founded(self) -> str:
        try:
            selectors_strategies = [
                ("dt h3", "founded"),
                (".text-heading-medium", "founded"),
                ("h3.text-heading-medium", "founded"),
            ]

            for selector, keyword in selectors_strategies:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if keyword in element.text.lower():
                            try:
                                dd_element = element.find_element(
                                    By.XPATH, "./../../following-sibling::dd"
                                )
                                founded = dd_element.text.strip()
                                if founded and self._is_valid_year(founded):
                                    return founded
                            except:
                                try:
                                    parent = element.find_element(By.XPATH, "./../..")
                                    dd_element = parent.find_element(
                                        By.XPATH, "./following-sibling::dd"
                                    )
                                    founded = dd_element.text.strip()
                                    if founded and self._is_valid_year(founded):
                                        return founded
                                except:
                                    continue
                except Exception:
                    continue

            fallback_selectors = [
                "dd.mb4.t-black--light.text-body-medium",
                ".t-black--light.text-body-medium",
            ]

            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and self._is_valid_year(text):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _is_valid_year(self, text: str) -> bool:
        year_pattern = r"\b(19|20)\d{2}\b"
        return bool(re.search(year_pattern, text))

    def _extract_company_size(self) -> str:
        try:
            selectors_strategies = [
                ("dt h3", "company size"),
                (".text-heading-medium", "company size"),
                ("h3.text-heading-medium", "company size"),
            ]

            for selector, keyword in selectors_strategies:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if keyword in element.text.lower():
                            try:
                                dd_element = element.find_element(
                                    By.XPATH, "./../../following-sibling::dd"
                                )
                                size = dd_element.text.strip()
                                if size and self._contains_employee_range(size):
                                    return size
                            except:
                                try:
                                    parent = element.find_element(By.XPATH, "./../..")
                                    dd_element = parent.find_element(
                                        By.XPATH, "./following-sibling::dd"
                                    )
                                    size = dd_element.text.strip()
                                    if size and self._contains_employee_range(size):
                                        return size
                                except:
                                    continue
                except Exception:
                    continue

            fallback_selectors = [
                "dd.t-black--light.text-body-medium.mb1",
                "dd.mb4.t-black--light.text-body-medium",
                ".t-black--light.text-body-medium",
            ]

            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and self._contains_employee_range(text):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _extract_associated_members(self) -> str:
        try:
            selectors = [
                "a[href*='currentCompany'] span",
                ".text-body-medium.t-black--light.link-without-visited-state span",
                "dd.t-black--light.mb4.text-body-medium a span",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if "associated members" in text.lower():
                            return text
                        elif self._is_member_count(text):
                            parent_element = element.find_element(By.XPATH, "./..")
                            parent_text = parent_element.text.strip()
                            if "associated members" in parent_text.lower():
                                return parent_text
                except Exception:
                    continue

            xpath_selectors = [
                "//a[contains(@href, 'currentCompany')]",
                "//dd[contains(text(), 'associated members')]",
                "//span[contains(text(), 'associated members')]",
            ]

            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        text = element.text.strip()
                        if text and "associated members" in text.lower():
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _is_member_count(self, text: str) -> bool:
        patterns = [r"\d+,\d+", r"\d+\.\d+K", r"\d+K", r"\d+M"]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_verified_date(self) -> str:
        try:
            selectors_strategies = [
                ("dt h3", "verified page"),
                (".text-heading-medium", "verified page"),
                ("h3.text-heading-medium", "verified page"),
                ("h3.inline.text-heading-medium", "verified page"),
            ]

            for selector, keyword in selectors_strategies:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if keyword in element.text.lower():
                            try:
                                dd_element = element.find_element(
                                    By.XPATH, "./../../following-sibling::dd"
                                )
                                verified_date = dd_element.text.strip()
                                if verified_date and self._is_valid_date(verified_date):
                                    return verified_date
                            except:
                                try:
                                    parent = element.find_element(By.XPATH, "./../..")
                                    dd_element = parent.find_element(
                                        By.XPATH, "./following-sibling::dd"
                                    )
                                    verified_date = dd_element.text.strip()
                                    if verified_date and self._is_valid_date(verified_date):
                                        return verified_date
                                except:
                                    continue
                except Exception:
                    continue

            fallback_selectors = [
                "dd.mb4.t-black--light.text-body-medium",
                ".t-black--light.text-body-medium",
            ]

            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and self._is_valid_date(text):
                            return text
                except Exception:
                    continue

            return "N/A"
        except Exception:
            return "N/A"

    def _is_valid_date(self, text: str) -> bool:
        date_patterns = [
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
            r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        ]

        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _wait_for_company_page(self) -> bool:
        try:
            self.wait.until(lambda driver: driver.current_url != "about:blank")

            current_url = self.driver.current_url
            if "linkedin.com/company/" not in current_url:
                return False

            company_indicators = [
                ".org-top-card-summary__title",
                ".org-top-card__primary-content",
                "h1[class*='org-top-card-summary__title']",
                ".org-top-card-summary-info-list",
            ]

            for selector in company_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        return True
                except Exception:
                    continue

            page_source = self.driver.page_source.lower()
            company_keywords = ["org-top-card", "company", "organization", "followers"]

            return any(keyword in page_source for keyword in company_keywords)

        except Exception:
            return False

    def _wait_for_about_page(self) -> bool:
        try:
            about_indicators = [
                ".org-about-module__margin-bottom",
                "h2:contains('Overview')",
                ".overflow-hidden dl",
                "dt h3",
            ]

            for selector in about_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return True
                except Exception:
                    continue

            page_source = self.driver.page_source.lower()
            about_keywords = ["overview", "website", "industry", "headquarters", "founded"]

            return any(keyword in page_source for keyword in about_keywords)

        except Exception:
            return False
