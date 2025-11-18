import re
from typing import Any

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from linkedin_spider.scrapers.base import BaseScraper
from linkedin_spider.utils.pattern_detector import PatternDetector


class ProfileScraper(BaseScraper):
    """Scraper for LinkedIn profiles."""

    def __init__(self, driver: Any, wait: Any, human_behavior: Any, tracking_handler: Any) -> None:
        super().__init__(driver, wait, human_behavior, tracking_handler)
        self.pattern_detector = PatternDetector()

    def _find_element_in_parent(self, parent: WebElement, by: By, value: str) -> WebElement | None:
        """Find element within parent element."""
        try:
            return parent.find_element(by, value)
        except Exception:
            return None

    def _is_valid_linkedin_url(self, url: str) -> bool:
        if not url or not isinstance(url, str) or url == "N/A":
            return False
        linkedin_pattern = r"^https?://(www\.)?linkedin\.com/in/"
        return bool(re.match(linkedin_pattern, url))

    def scrape_profile(self, profile_url: str) -> dict[str, Any] | None:
        """Scrape a LinkedIn profile."""
        return self.scrape(profile_url)

    def scrape(self, profile_url: str) -> dict[str, Any] | None:
        """Main scraping implementation."""
        if not self._is_valid_linkedin_url(profile_url):
            self.log_action("ERROR", f"Invalid profile URL: {profile_url}")
            return None

        self.log_action("INFO", f"Scraping profile: {profile_url}")

        try:
            self.driver.get(profile_url)

            if not self._wait_for_profile_page():
                self.log_action("ERROR", f"Failed to load profile page: {profile_url}")
                return None

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_behavior.delay(0.5, 1)

            profile_data = {}
            profile_data["name"] = self._extract_name()
            profile_data["headline"] = self._extract_headline()
            profile_data["location"] = self._extract_location()
            profile_data["about"] = self._extract_about()
            profile_data["experience"] = self._extract_experience()
            profile_data["education"] = self._extract_education()
            profile_data["profile_url"] = profile_url

            self.human_behavior.delay(1, 2)

            self.log_action(
                "SUCCESS", f"Successfully scraped profile: {profile_data.get('name', 'Unknown')}"
            )

            return profile_data

        except Exception as e:
            self.log_action("ERROR", f"Error scraping profile {profile_url}: {e!s}")
            return None

    def _extract_name(self) -> str:
        try:
            name_selectors = [
                "h1.inline.t-24.v-align-middle.break-words",
                "h1.text-heading-xlarge",
                ".artdeco-entity-lockup__title",
            ]

            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name_text = name_element.text.strip()
                    if name_text and len(name_text) > 2:
                        return name_text
                except NoSuchElementException:
                    continue

            return "N/A"

        except Exception:
            return "N/A"

    def _extract_headline(self) -> str:
        try:
            selectors = [
                ".text-body-medium.break-words",
                ".artdeco-entity-lockup__subtitle",
                ".pv-text-details__left-panel .text-body-medium",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text and len(text) > 5:
                        return text
                except NoSuchElementException:
                    continue

            return "N/A"

        except Exception:
            return "N/A"

    def _extract_location(self) -> str:
        try:
            selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small",
                "[class*='t-black--light'].text-body-small",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text:
                        return text
                except NoSuchElementException:
                    continue

            return "N/A"

        except Exception:
            return "N/A"

    def _extract_about(self) -> str:
        try:
            about_section = self._find_section_by_heading(["About"])
            if about_section:
                selectors = [
                    "[class*='inline-show-more-text'] span[aria-hidden='true']",
                    ".pv-shared-text-with-see-more",
                    ".visually-hidden",
                ]
                for selector in selectors:
                    try:
                        element = about_section.find_element(By.CSS_SELECTOR, selector)
                        text = element.text.strip()
                        if text and (selector != ".visually-hidden"):
                            return text
                    except NoSuchElementException:
                        continue

            for selector in [
                "[class*='inline-show-more-text'] span[aria-hidden='true']",
                ".pv-shared-text-with-see-more",
            ]:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text:
                        return text
                except NoSuchElementException:
                    continue

            return "N/A"

        except Exception:
            return "N/A"

    def _extract_experience(self) -> list[dict[str, str]]:
        experience_list = []

        try:
            experience_section = self._find_section_by_heading(["Experience"])
            if not experience_section:
                return experience_list

            experience_containers = experience_section.find_elements(
                By.CSS_SELECTOR, "[data-view-name='profile-component-entity']"
            )

            for container in experience_containers[:8]:
                exp_data = self._extract_experience_item(container)
                if exp_data and (
                    exp_data.get("title") != "N/A" or exp_data.get("company") != "N/A"
                ):
                    experience_list.append(exp_data)

        except Exception as e:
            self.log_action("ERROR", f"Error scraping experience: {e!s}")

        return experience_list

    def _extract_experience_item(self, container: WebElement) -> dict[str, str]:
        exp_data = {
            "title": "N/A",
            "company": "N/A",
            "company_url": "N/A",
            "duration": "N/A",
            "location": "N/A",
        }

        try:
            title_selectors = [
                "[class*='hoverable-link-text'].t-bold span[aria-hidden='true']",
                ".mr1.t-bold span[aria-hidden='true']",
                ".t-bold span[aria-hidden='true']",
            ]

            for selector in title_selectors:
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_element.text.strip()
                    if title_text and len(title_text) > 2:
                        exp_data["title"] = title_text
                        break
                except Exception:
                    continue
        except Exception:
            pass

        try:
            company_link = container.find_element(
                By.CSS_SELECTOR, "a[data-field='experience_company_logo']"
            )
            exp_data["company_url"] = company_link.get_attribute("href")

            company_selectors = [
                "a[data-field='experience_company_logo'] span[aria-hidden='true']",
                "[class*='hoverable-link-text'] span[aria-hidden='true']",
            ]

            for selector in company_selectors:
                try:
                    company_element = container.find_element(By.CSS_SELECTOR, selector)
                    company_text = company_element.text.strip()
                    if company_text and len(company_text) > 2:
                        exp_data["company"] = company_text
                        break
                except Exception:
                    continue
        except Exception:
            pass

        try:
            duration_selectors = [
                ".t-14.t-normal span[aria-hidden='true']",
                ".pvs-entity__caption-wrapper span[aria-hidden='true']",
                "[class*='t-black--light'] span[aria-hidden='true']",
            ]

            for selector in duration_selectors:
                try:
                    duration_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in duration_elements:
                        duration_text = element.text.strip()
                        if duration_text and any(
                            x in duration_text.lower()
                            for x in [
                                "present",
                                "mos",
                                "yrs",
                                "month",
                                "year",
                                "jan",
                                "feb",
                                "mar",
                                "apr",
                                "may",
                                "jun",
                                "jul",
                                "aug",
                                "sep",
                                "oct",
                                "nov",
                                "dec",
                            ]
                        ):
                            exp_data["duration"] = duration_text
                            break
                    if exp_data["duration"] != "N/A":
                        break
                except Exception:
                    continue
        except Exception:
            pass

        try:
            location_selectors = [
                ".pvs-entity__caption-wrapper span[aria-hidden='true']",
                "[class*='t-black--light'] span[aria-hidden='true']",
            ]

            for selector in location_selectors:
                try:
                    location_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in location_elements:
                        location_text = element.text.strip()
                        if (
                            location_text
                            and self.pattern_detector.is_likely_location(location_text)
                            and not self.pattern_detector.is_time_duration(location_text)
                        ):
                            exp_data["location"] = location_text
                            break
                    if exp_data["location"] != "N/A":
                        break
                except Exception:
                    continue
        except Exception:
            pass
        return exp_data

    def _extract_education(self) -> list[dict[str, str]]:
        education_list = []

        try:
            education_section = self._find_section_by_heading(["Education"])
            if not education_section:
                return education_list

            education_containers = education_section.find_elements(
                By.CSS_SELECTOR, "[data-view-name='profile-component-entity']"
            )

            for container in education_containers[:5]:
                edu_data = self._extract_education_item(container)
                if edu_data and edu_data.get("school") != "N/A":
                    education_list.append(edu_data)

        except Exception as e:
            self.log_action("ERROR", f"Error scraping education: {e!s}")

        return education_list

    def _extract_education_item(self, container: WebElement) -> dict[str, str]:
        edu_data = {
            "school": "N/A",
            "degree": "N/A",
            "field_of_study": "N/A",
            "duration": "N/A",
            "grade": "N/A",
        }

        try:
            school_selectors = [
                "[class*='hoverable-link-text'].t-bold span[aria-hidden='true']",
                ".t-bold span[aria-hidden='true']",
            ]

            for selector in school_selectors:
                try:
                    school_element = container.find_element(By.CSS_SELECTOR, selector)
                    school_text = school_element.text.strip()
                    if school_text and len(school_text) > 2:
                        edu_data["school"] = school_text
                        break
                except Exception:
                    continue
        except Exception:
            pass

        try:
            degree_selectors = [
                ".t-14.t-normal span[aria-hidden='true']",
                "[class*='t-normal'] span[aria-hidden='true']",
            ]

            for selector in degree_selectors:
                try:
                    degree_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in degree_elements:
                        degree_text = element.text.strip()
                        if (
                            degree_text
                            and len(degree_text) > 3
                            and self.pattern_detector.is_likely_degree(degree_text)
                        ):
                            if "," in degree_text:
                                parts = degree_text.split(",", 1)
                                edu_data["degree"] = parts[0].strip()
                                if len(parts) > 1:
                                    edu_data["field_of_study"] = parts[1].strip()
                            else:
                                edu_data["degree"] = degree_text
                            break
                    if edu_data["degree"] != "N/A":
                        break
                except Exception:
                    continue
        except Exception:
            pass

        try:
            duration_selectors = [
                ".pvs-entity__caption-wrapper span[aria-hidden='true']",
                "[class*='t-black--light'] span[aria-hidden='true']",
            ]

            for selector in duration_selectors:
                try:
                    duration_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in duration_elements:
                        duration_text = element.text.strip()
                        if (
                            duration_text
                            and any(year in duration_text for year in ["201", "202", "200"])
                            and ("-" in duration_text or "to" in duration_text.lower())
                        ):
                            edu_data["duration"] = duration_text
                            break
                    if edu_data["duration"] != "N/A":
                        break
                except Exception:
                    continue
        except Exception:
            pass

        try:
            grade_selectors = [
                "[class*='inline-show-more-text'] span[aria-hidden='true']",
                ".t-14.t-normal.t-black span[aria-hidden='true']",
            ]

            for selector in grade_selectors:
                try:
                    grade_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in grade_elements:
                        grade_text = element.text.strip()
                        if grade_text and (
                            "grade:" in grade_text.lower()
                            or "/" in grade_text
                            or "gpa" in grade_text.lower()
                        ):
                            edu_data["grade"] = grade_text
                            break
                    if edu_data["grade"] != "N/A":
                        break
                except Exception:
                    continue
        except Exception:
            pass

        return edu_data

    def _find_section_by_heading(self, headings: list[str]) -> WebElement | None:
        try:
            for heading in headings:
                section_selectors = [
                    f"//h2[contains(text(), '{heading}')]/ancestor::section",
                    f"//h2/span[contains(text(), '{heading}')]/ancestor::section",
                    "//div[@id='experience']/ancestor::section",
                    "//div[@id='education']/ancestor::section",
                ]

                for selector in section_selectors:
                    try:
                        if "experience" in heading.lower() and "experience" not in selector:
                            continue
                        if "education" in heading.lower() and "education" not in selector:
                            continue

                        section = self.driver.find_element(By.XPATH, selector)
                        return section
                    except Exception:
                        continue

            fallback_selectors = [
                "section:has(h2):has(.pvs-list__paged-list-item)",
                ".pv-profile-section.experience",
                ".pv-profile-section.education",
            ]

            for selector in fallback_selectors:
                try:
                    section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return section
                except Exception:
                    continue

        except Exception:
            pass

        return None

    def _wait_for_profile_page(self) -> bool:
        try:
            self.wait.until(lambda driver: driver.current_url != "about:blank")

            current_url = self.driver.current_url
            if "linkedin.com/in/" not in current_url:
                return False

            profile_indicators = [
                "h1[data-test-id='profile-name']",
                "h1.text-heading-xlarge",
                ".pv-text-details__left-panel h1",
                "h1.top-card-layout__title",
                ".artdeco-entity-lockup__title",
                "main[role='main']",
                ".pv-profile-section",
            ]

            for selector in profile_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        return True
                except Exception:
                    continue

            page_source = self.driver.page_source.lower()
            profile_keywords = ["profile", "experience", "education", "about", "contact info"]

            return any(keyword in page_source for keyword in profile_keywords)

        except Exception:
            return False
