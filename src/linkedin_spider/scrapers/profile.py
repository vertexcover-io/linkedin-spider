import logging
import re
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from linkedin_spider.scrapers.base import BaseScraper
from linkedin_spider.utils.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)

_DURATION_KEYWORDS = [
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


class ProfileScraper(BaseScraper):
    """Scraper for LinkedIn profiles.

    LinkedIn's current DOM uses obfuscated/hashed CSS class names that change
    frequently. This scraper avoids class-based selectors and instead relies on:
    - document.title for the profile name
    - Section headings (h2) to locate profile sections
    - data-view-name attributes where available
    - Positional p-tag extraction within known section structures
    - Content pattern matching (dates, locations, degrees) for field identification
    """

    def __init__(self, driver: Any, wait: Any, human_behavior: Any, tracking_handler: Any) -> None:
        super().__init__(driver, wait, human_behavior, tracking_handler)
        self.pattern_detector = PatternDetector()

    def _is_valid_linkedin_url(self, url: str) -> bool:
        if not url or not isinstance(url, str) or url == "N/A":
            return False
        return bool(re.match(r"^https?://(www\.)?linkedin\.com/in/", url))

    def scrape_profile(self, profile_url: str) -> dict[str, Any] | None:
        return self.scrape(profile_url)

    def scrape(self, profile_url: str) -> dict[str, Any] | None:
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

            name = self._extract_name()
            profile_section = self._find_profile_section(name)

            profile_data: dict[str, Any] = {}
            profile_data["name"] = name
            profile_data["headline"] = self._extract_headline(profile_section)
            profile_data["location"] = self._extract_location(profile_section)
            profile_data["about"] = self._extract_about()
            profile_data["experience"] = self._extract_experience()
            profile_data["education"] = self._extract_education()
            profile_data["profile_url"] = profile_url

            self.human_behavior.delay(1, 2)

            self.log_action(
                "SUCCESS", f"Successfully scraped profile: {profile_data.get('name', 'Unknown')}"
            )
        except Exception as e:
            self.log_action("ERROR", f"Error scraping profile {profile_url}: {e!s}")
            return None
        else:
            return profile_data

    # ── Name ──────────────────────────────────────────────────────────────

    def _extract_name(self) -> str:
        """Extract name from page title ('Name | LinkedIn') with DOM fallbacks."""
        try:
            title = self.driver.title or ""
            match = re.match(r"^(.+?)\s*\|\s*LinkedIn", title)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:
                    return name
        except Exception:
            logger.debug("Failed to extract name from title")

        # Fallback: find the first h2 inside a section that looks like a profile card
        try:
            sections = self.driver.find_elements(By.TAG_NAME, "section")
            for section in sections[:5]:
                h2 = self._find_child(section, By.TAG_NAME, "h2")
                if not h2:
                    continue
                h2_text = h2.text.strip()
                # Profile section h2 is the person's name (not "Experience", "Education", etc.)
                if (
                    h2_text
                    and len(h2_text) > 2
                    and h2_text
                    not in {
                        "Highlights",
                        "Activity",
                        "Experience",
                        "Education",
                        "Skills",
                        "Recommendations",
                        "Interests",
                        "About",
                        "Licenses & certifications",
                        "Projects",
                        "Volunteering",
                        "Publications",
                        "Patents",
                        "Courses",
                        "Test scores",
                        "Languages",
                        "Causes",
                    }
                ):
                    return h2_text
        except Exception:
            logger.debug("Failed to extract name from section h2")

        return "N/A"

    # ── Profile section discovery ─────────────────────────────────────────

    def _find_profile_section(self, name: str) -> WebElement | None:
        """Find the profile top-card section by matching its h2 to the extracted name."""
        if not name or name == "N/A":
            return None
        try:
            sections = self.driver.find_elements(By.TAG_NAME, "section")
            for section in sections[:5]:
                h2 = self._find_child(section, By.TAG_NAME, "h2")
                if h2 and h2.text.strip() == name:
                    return section
        except Exception:
            logger.debug("Failed to find profile section")
        return None

    # ── Headline ──────────────────────────────────────────────────────────

    def _extract_headline(self, profile_section: WebElement | None) -> str:
        if not profile_section:
            return "N/A"
        try:
            ps = profile_section.find_elements(By.TAG_NAME, "p")
            for p in ps:
                text = p.text.strip()
                # Skip short/noise text: connection degree ("· 2nd"), dots, numbers
                if not text or len(text) <= 3:
                    continue
                if text.startswith("·"):
                    continue
                if re.match(r"^\d+\+?$", text):
                    continue
                if text.lower() in {"connections", "connection", "contact info"}:
                    continue
                # First substantive p is the headline
                return text
        except Exception:
            logger.debug("Failed to extract headline from profile section")
        return "N/A"

    # ── Location ──────────────────────────────────────────────────────────

    def _extract_location(self, profile_section: WebElement | None) -> str:
        if not profile_section:
            return "N/A"
        try:
            ps = profile_section.find_elements(By.TAG_NAME, "p")
            # Skip the first substantive p (it's the headline), then find location
            skipped_headline = False
            for p in ps:
                text = p.text.strip()
                if not text or len(text) <= 3:
                    continue
                if not skipped_headline:
                    skipped_headline = True
                    continue
                if self.pattern_detector.is_likely_location(text):
                    return text
        except Exception:
            logger.debug("Failed to extract location from profile section")
        return "N/A"

    # ── About ─────────────────────────────────────────────────────────────

    def _extract_about(self) -> str:
        about_section = self._find_section_by_heading("About")
        if not about_section:
            return "N/A"

        try:
            # Get all p/span text within the about section, skip the heading itself
            for tag in ["p", "span"]:
                elements = about_section.find_elements(By.TAG_NAME, tag)
                for el in elements:
                    text = el.text.strip()
                    if text and len(text) > 20 and text != "About":
                        return text
        except Exception:
            logger.debug("Failed to extract about text")
        return "N/A"

    # ── Experience ────────────────────────────────────────────────────────

    def _extract_experience(self) -> list[dict[str, str]]:
        exp_section = self._find_section_by_heading("Experience")
        if not exp_section:
            return []

        try:
            return self._extract_experience_via_js(exp_section)
        except Exception as e:
            self.log_action("ERROR", f"Error scraping experience: {e!s}")
            return []

    def _extract_experience_via_js(self, exp_section: WebElement) -> list[dict[str, str]]:
        """Extract experience items using company logo links as anchors for grouping."""
        company_links = exp_section.find_elements(
            By.CSS_SELECTOR, "a[href*='/company/']"
        )

        if not company_links:
            # Fallback: parse all p tags in the section as a flat list
            return self._extract_experience_from_ps(exp_section)

        experience_list: list[dict[str, str]] = []
        seen_container_ids: set[str] = set()
        for link in company_links[:16]:
            try:
                container = self._find_item_container(link, exp_section)
                if not container:
                    continue

                # Deduplicate using JS-assigned unique ID
                container_id = self.driver.execute_script(
                    "if (!arguments[0]._spiderId) arguments[0]._spiderId = Math.random().toString(36); return arguments[0]._spiderId;",
                    container,
                )
                if container_id in seen_container_ids:
                    continue
                seen_container_ids.add(container_id)

                ps = [
                    p.text.strip()
                    for p in container.find_elements(By.TAG_NAME, "p")
                    if p.text.strip()
                ]
                company_url = link.get_attribute("href") or "N/A"
                exp_data = self._parse_experience_ps(ps, company_url)

                if exp_data.get("title") != "N/A" or exp_data.get("company") != "N/A":
                    experience_list.append(exp_data)
            except Exception:
                logger.debug("Failed to extract an experience item")
                continue

        return experience_list

    def _extract_experience_from_ps(self, section: WebElement) -> list[dict[str, str]]:
        """Fallback: extract experience from flat p-tag list when company links aren't found."""
        ps = [p.text.strip() for p in section.find_elements(By.TAG_NAME, "p") if p.text.strip()]
        if not ps:
            return []

        # Group p-tags into experience items: each group starts with a non-date, non-location line
        items: list[dict[str, str]] = []
        current_ps: list[str] = []
        for text in ps:
            if (
                current_ps
                and not self._is_duration(text)
                and not self._is_location_text(text)
                and "·" not in text
            ):
                # Start of a new item
                items.append(self._parse_experience_ps(current_ps, "N/A"))
                current_ps = []
            current_ps.append(text)

        if current_ps:
            items.append(self._parse_experience_ps(current_ps, "N/A"))

        return [
            item for item in items if item.get("title") != "N/A" or item.get("company") != "N/A"
        ]

    def _parse_experience_ps(self, ps: list[str], company_url: str) -> dict[str, str]:
        """Parse a list of p-tag texts into an experience dict.

        Typical order: [title, "company · employment_type", "date_range · duration", "location · work_type"]
        """
        exp: dict[str, str] = {
            "title": "N/A",
            "company": "N/A",
            "company_url": company_url,
            "duration": "N/A",
            "location": "N/A",
        }
        if not ps:
            return exp

        exp["title"] = ps[0]

        for text in ps[1:]:
            if exp["duration"] == "N/A" and self._is_duration(text):
                exp["duration"] = text
            elif exp["company"] == "N/A" and "·" in text and not self._is_duration(text):
                exp["company"] = text.split("·")[0].strip()
            elif exp["location"] == "N/A" and self._is_location_text(text):
                exp["location"] = text

        return exp

    # ── Education ─────────────────────────────────────────────────────────

    def _extract_education(self) -> list[dict[str, str]]:
        edu_section = self._find_section_by_heading("Education")
        if not edu_section:
            return []

        try:
            # Try grouping by school links first (more reliable)
            school_links = edu_section.find_elements(
                By.CSS_SELECTOR, "a[href*='/school/']"
            )
            if school_links:
                seen_container_ids: set[str] = set()
                education_list: list[dict[str, str]] = []
                for link in school_links[:10]:
                    container = self._find_item_container(link, edu_section)
                    if not container:
                        continue
                    container_id = self.driver.execute_script(
                        "if (!arguments[0]._spiderId) arguments[0]._spiderId = Math.random().toString(36); return arguments[0]._spiderId;",
                        container,
                    )
                    if container_id in seen_container_ids:
                        continue
                    seen_container_ids.add(container_id)
                    ps = [
                        p.text.strip()
                        for p in container.find_elements(By.TAG_NAME, "p")
                        if p.text.strip()
                    ]
                    if ps:
                        edu = self._parse_single_education(ps)
                        if edu["school"] != "N/A":
                            education_list.append(edu)
                return education_list[:5]

            # Fallback: parse all p tags
            ps = [
                p.text.strip()
                for p in edu_section.find_elements(By.TAG_NAME, "p")
                if p.text.strip()
            ]
            return self._parse_education_ps(ps)
        except Exception as e:
            self.log_action("ERROR", f"Error scraping education: {e!s}")
            return []

    def _parse_single_education(self, ps: list[str]) -> dict[str, str]:
        """Parse p-tags from a single education container into a structured dict."""
        edu = self._empty_education()
        if not ps:
            return edu

        edu["school"] = ps[0]
        for text in ps[1:]:
            if self._is_year_range(text):
                edu["duration"] = text
            elif self._is_grade(text):
                edu["grade"] = text
            elif text.lower().startswith("activities and societies"):
                continue
            elif self.pattern_detector.is_likely_degree(text):
                if "," in text:
                    parts = text.split(",", 1)
                    edu["degree"] = parts[0].strip()
                    edu["field_of_study"] = parts[1].strip()
                else:
                    edu["degree"] = text
        return edu

    def _parse_education_ps(self, ps: list[str]) -> list[dict[str, str]]:
        """Parse education p-tags into structured items.

        Typical patterns per item:
        - School name (not a date, not a degree keyword)
        - Degree line (contains degree keywords like Bachelor, Master, MBA, etc.)
        - Duration (year range like "2014 - 2018")
        - Grade (contains "grade:", "gpa", or "/")
        """
        items: list[dict[str, str]] = []
        current: dict[str, str] = self._empty_education()

        for text in ps:
            if self._is_year_range(text):
                current["duration"] = text
            elif self._is_grade(text):
                current["grade"] = text
            elif self.pattern_detector.is_likely_degree(text):
                if "," in text:
                    parts = text.split(",", 1)
                    current["degree"] = parts[0].strip()
                    current["field_of_study"] = parts[1].strip()
                else:
                    current["degree"] = text
            elif text.lower().startswith("activities and societies"):
                # Supplementary info — attach to current item, skip
                continue
            else:
                # Not a date/degree/grade → likely a school name → starts a new item
                if current["school"] != "N/A":
                    items.append(current)
                    current = self._empty_education()
                current["school"] = text

        if current["school"] != "N/A":
            items.append(current)

        return items[:5]

    @staticmethod
    def _empty_education() -> dict[str, str]:
        return {
            "school": "N/A",
            "degree": "N/A",
            "field_of_study": "N/A",
            "duration": "N/A",
            "grade": "N/A",
        }

    # ── Section discovery ─────────────────────────────────────────────────

    def _find_section_by_heading(self, heading: str) -> WebElement | None:
        """Find a section element whose h2 text matches the given heading."""
        try:
            xpath = f"//h2[normalize-space(text())='{heading}']/ancestor::section"
            return self.driver.find_element(By.XPATH, xpath)
        except Exception:
            logger.debug("Section not found via h2 text for: %s", heading)

        try:
            xpath = f"//h2/span[normalize-space(text())='{heading}']/ancestor::section"
            return self.driver.find_element(By.XPATH, xpath)
        except Exception:
            logger.debug("Section not found via h2/span text for: %s", heading)

        return None

    # ── Page load detection ───────────────────────────────────────────────

    def _wait_for_profile_page(self) -> bool:
        try:
            self.wait.until(lambda driver: driver.current_url != "about:blank")

            current_url = self.driver.current_url
            if "linkedin.com/in/" not in current_url:
                return False

            # Wait for the title to contain " | LinkedIn"
            try:
                self.wait.until(lambda driver: "| LinkedIn" in (driver.title or ""))
            except Exception:
                logger.debug("Title wait timed out, falling back to page source check")
            else:
                return True

            # Fallback: check page source for profile keywords
            page_source = self.driver.page_source.lower()
            return any(kw in page_source for kw in ["experience", "education", "contact info"])

        except Exception:
            return False

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _find_child(parent: WebElement, by: str, value: str) -> WebElement | None:
        try:
            el: WebElement = parent.find_element(by, value)
        except Exception:
            return None
        else:
            return el

    def _find_item_container(self, child: WebElement, boundary: WebElement) -> WebElement | None:
        """Walk up from child to find the nearest container with siblings (list item pattern)."""
        try:
            result: WebElement | None = self.driver.execute_script(
                """
                let el = arguments[0].parentElement;
                const boundary = arguments[1];
                for (let i = 0; i < 10 && el && el !== boundary; i++) {
                    const parent = el.parentElement;
                    if (parent && parent.children.length > 1) return el;
                    el = parent;
                }
                return el;
            """,
                child,
                boundary,
            )
        except Exception:
            return None
        else:
            return result

    @staticmethod
    def _is_duration(text: str) -> bool:
        lower = text.lower()
        return any(kw in lower for kw in _DURATION_KEYWORDS)

    def _is_location_text(self, text: str) -> bool:
        return bool(self.pattern_detector.is_likely_location(text))

    @staticmethod
    def _is_year_range(text: str) -> bool:
        return bool(re.search(r"\b(19|20)\d{2}\b", text) and ("\u2013" in text or "-" in text))

    @staticmethod
    def _is_grade(text: str) -> bool:
        lower = text.lower()
        return "grade:" in lower or "gpa" in lower
