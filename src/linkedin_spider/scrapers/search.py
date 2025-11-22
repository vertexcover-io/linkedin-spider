import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.scrapers.base import BaseScraper
from linkedin_spider.scrapers.search_filters import SearchFilterHandler


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
        except Exception:  # noqa: S110
            # Silently ignore scroll errors as they're non-critical
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

                except Exception as e:
                    self.log_action(
                        "WARNING", f"Failed to extract anonymous data from container: {e!s}"
                    )
                    continue

        except Exception:
            return []
        else:
            return results

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
                    except Exception:
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

                except Exception as e:
                    self.log_action("WARNING", f"Failed to extract profile from container: {e!s}")
                    continue

        except Exception as e:
            self.log_action("ERROR", f"Search failed: {e!s}")
            return []
        else:
            self.log_action("SUCCESS", f"Found {len(results)} profiles for query: {query}")
            return results

    def get_applied_filters(self) -> Any:
        return self.filter_handler.get_applied_filters()

    def reset_filters(self) -> Any:
        return self.filter_handler.reset_filters()

    def search_posts(
        self,
        keywords: str,
        max_results: int = 10,
        scroll_pause: float = 2.0,
        max_comments: int = 10,
        date_posted: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for LinkedIn posts by keywords.

        Args:
            keywords: Search keywords
            max_results: Maximum number of posts to scrape
            scroll_pause: Pause duration between scrolls (seconds)
            max_comments: Maximum number of comments to fetch per post (0 to skip comments)
            date_posted: Filter by date posted. Valid values: "past-24h", "past-week", "past-month", or None

        Returns:
            List of post data dictionaries
        """
        try:
            # Build search URL for content
            encoded_keywords = urllib.parse.quote(keywords)
            search_url = (
                f"https://www.linkedin.com/search/results/content/?keywords={encoded_keywords}"
            )

            # Add date filter to URL if provided
            if date_posted:
                valid_filters = ["past-24h", "past-week", "past-month"]
                if date_posted in valid_filters:
                    search_url += f'&datePosted="{date_posted}"'
                    self.log_action("INFO", f"Applying date filter: {date_posted}")
                else:
                    self.log_action(
                        "WARNING",
                        f"Invalid date_posted value: {date_posted}. Must be one of {valid_filters}",
                    )

            self.log_action("INFO", f"Searching for posts with keywords: {keywords}")

            if not self.navigate_to_url(search_url):
                self.log_action("ERROR", f"Failed to navigate to post search: {keywords}")
                return []

            self.log_action("INFO", f"Navigated to post search URL: {search_url}")

            # Wait for initial page load
            self.human_behavior.delay(2.0, 4.0)

            # Step 1: Scroll to load all required post containers
            self.log_action("INFO", "Loading post containers...")
            post_containers = self._load_post_containers(max_results, scroll_pause)

            if not post_containers:
                self.log_action("WARNING", "No post containers found")
                return []

            self.log_action("INFO", f"Loaded {len(post_containers)} post containers")

            # Step 2: Parse all loaded posts
            posts_data = []
            seen_posts = set()

            for container in post_containers[:max_results]:
                try:
                    # Extract a unique identifier to avoid duplicates
                    post_id = self._extract_post_id(container)
                    if post_id and post_id in seen_posts:
                        continue

                    # Extract post data
                    post_data = self._extract_post_data(container, max_comments=max_comments)

                    # Only add if we got meaningful data
                    if post_data and post_data.get("author_name") != "N/A":
                        if post_id:
                            seen_posts.add(post_id)
                        posts_data.append(post_data)
                        self.log_action(
                            "INFO",
                            f"Extracted post {len(posts_data)}/{max_results} by {post_data.get('author_name')}",
                        )

                except Exception as e:
                    self.log_action("WARNING", f"Failed to extract post data: {e!s}")
                    continue

        except Exception as e:
            self.log_action("ERROR", f"Post search failed: {e!s}")
            return []
        else:
            self.log_action(
                "SUCCESS", f"Extracted {len(posts_data)} posts for keywords: {keywords}"
            )
            return posts_data

    def _find_post_containers(self) -> list[WebElement]:
        """Find all post containers on the page."""
        # Try multiple selectors for post containers
        selectors = [
            "div.feed-shared-update-v2__control-menu-container",
            "div.update-components-update-v2",
            "div[data-urn*='activity']",
        ]

        for selector in selectors:
            containers = self._find_elements_safe(By.CSS_SELECTOR, selector, timeout=5)
            if containers:
                return containers

        return []

    def _load_post_containers(self, max_results: int, scroll_pause: float) -> list[WebElement]:
        """
        Scroll and load post containers until we have enough posts.

        Args:
            max_results: Target number of posts to load
            scroll_pause: Pause duration between scrolls

        Returns:
            List of post container WebElements
        """
        all_containers = []
        previous_count = 0
        scroll_attempts = 0
        max_scroll_attempts = max_results * 2  # Allow more scrolls to find posts
        stale_scroll_count = 0  # Track consecutive scrolls with no new posts

        while len(all_containers) < max_results and scroll_attempts < max_scroll_attempts:
            # Find current post containers
            current_containers = self._find_post_containers()

            if current_containers:
                # Use a set to track unique containers and avoid duplicates
                # We'll identify containers by their location or URN
                unique_containers = []
                seen_ids = set()

                for container in current_containers:
                    try:
                        # Get a unique identifier for this container
                        container_id = self._extract_post_id(container)
                        if not container_id:
                            # Fallback: use element location as identifier
                            container_id = f"{container.location['x']}_{container.location['y']}"

                        if container_id not in seen_ids:
                            seen_ids.add(container_id)
                            unique_containers.append(container)
                    except Exception:
                        # If we can't get an ID, just add it
                        unique_containers.append(container)

                all_containers = unique_containers

                # Check if we found new posts
                if len(all_containers) == previous_count:
                    stale_scroll_count += 1
                    # If we haven't found new posts after 3 scrolls, stop
                    if stale_scroll_count >= 3:
                        self.log_action(
                            "INFO",
                            f"No new posts found after {stale_scroll_count} scrolls. Stopping at {len(all_containers)} posts.",
                        )
                        break
                else:
                    stale_scroll_count = 0
                    previous_count = len(all_containers)

                self.log_action("INFO", f"Loaded {len(all_containers)} post containers so far...")

            # Scroll to load more posts
            if len(all_containers) < max_results:
                self.log_action(
                    "INFO",
                    f"Scrolling to load more posts... (attempt {scroll_attempts + 1}/{max_scroll_attempts})",
                )
                self._scroll_and_wait(500)
                self.log_action("INFO", f"Waiting {scroll_pause}s for new posts to load...")
                self.human_behavior.delay(scroll_pause, scroll_pause + 1.0)
                scroll_attempts += 1
            else:
                break

        return all_containers

    def _extract_post_id(self, container: WebElement) -> str | None:
        """Extract a unique identifier for the post to avoid duplicates."""
        try:
            # Try to get URN from data attributes
            urn = self._extract_attribute_safe(container, "data-urn")
            if urn:
                return urn

            # Try to find post link
            link_elem = self._find_element_in_parent(
                container, By.CSS_SELECTOR, "a[href*='/feed/update/']"
            )
            if link_elem:
                href = self._extract_attribute_safe(link_elem, "href")
                if href:
                    return href

        except Exception:
            return None
        else:
            return None

    def _extract_post_data(self, container: WebElement, max_comments: int = 10) -> dict[str, Any]:
        """
        Extract comprehensive data from a post container.

        Args:
            container: Post container WebElement
            max_comments: Maximum number of comments to fetch (0 to skip comments)

        Returns:
            Dictionary containing post data with keys:
            - author_name
            - author_headline
            - author_profile_url
            - connection_degree (e.g., "1st", "2nd", "3rd+")
            - post_time (ISO 8601 UTC timestamp)
            - post_text (markdown format with links)
            - hashtags
            - links (list of external domain URLs only - excludes internal LinkedIn links)
            - post_url
            - media_urls (list of image/video URLs)
            - likes_count
            - comments_count
            - reposts_count
            - comments (list of comment dictionaries, empty if max_comments=0)
        """
        post_data = {
            "author_name": "N/A",
            "author_headline": "N/A",
            "author_profile_url": "N/A",
            "connection_degree": "N/A",
            "post_time": "N/A",
            "post_text": "N/A",
            "hashtags": [],
            "links": [],
            "post_url": "N/A",
            "media_urls": [],
            "likes_count": 0,
            "comments_count": 0,
            "reposts_count": 0,
            "comments": [],
        }

        try:
            # Extract author information
            author_info = self._extract_author_info(container)
            post_data.update(author_info)

            # Extract post content
            post_content = self._extract_post_content(container)
            post_data.update(post_content)

            # Extract engagement metrics
            engagement = self._extract_engagement_metrics(container)
            post_data.update(engagement)

            # Extract post URL
            post_url = self._extract_post_url(container)
            if post_url:
                post_data["post_url"] = post_url

            # Extract media URLs (images and videos) if present
            media_urls = self._extract_post_media(container)
            if media_urls:
                post_data["media_urls"] = media_urls

            # Extract comments if max_comments > 0
            if max_comments > 0:
                comments = self._extract_post_comments(container, max_comments)
                if comments:
                    post_data["comments"] = comments

        except Exception as e:
            self.log_action("WARNING", f"Error extracting post data: {e!s}")

        return post_data

    def _extract_author_info(self, container: WebElement) -> dict[str, Any]:
        """Extract author name, headline, profile URL, and connection degree."""
        author_info = {
            "author_name": "N/A",
            "author_headline": "N/A",
            "author_profile_url": "N/A",
            "connection_degree": "N/A",
        }

        try:
            # Find the actor/author container
            actor_selectors = [
                ".update-components-actor__container",
                ".update-components-actor",
                ".feed-shared-actor",
            ]

            actor_container = None
            for selector in actor_selectors:
                actor_container = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if actor_container:
                    break

            if not actor_container:
                return author_info

            # Extract author name and profile URL
            name_link_selectors = [
                "a.update-components-actor__meta-link",
                "a[data-view-name='search-result-lockup-title']",
                "a.app-aware-link[href*='/in/']",
            ]

            for selector in name_link_selectors:
                name_link = self._find_element_in_parent(actor_container, By.CSS_SELECTOR, selector)
                if name_link:
                    # Extract profile URL
                    profile_url = self._extract_attribute_safe(name_link, "href")
                    if profile_url and "/in/" in profile_url:
                        # Clean up URL (remove query parameters)
                        author_info["author_profile_url"] = profile_url.split("?")[0]

                    # Extract name from aria-hidden span to avoid duplicates
                    name_elem = self._find_element_in_parent(
                        name_link, By.CSS_SELECTOR, 'span[aria-hidden="true"]'
                    )
                    if name_elem:
                        name_text = self._extract_text_safe(name_elem)
                        # Clean up any duplicates or extra whitespace
                        name_lines = [
                            line.strip() for line in name_text.split("\n") if line.strip()
                        ]
                        # Get unique lines preserving order
                        seen = set()
                        unique_lines = []
                        for line in name_lines:
                            if line not in seen and not line.startswith("•"):
                                seen.add(line)
                                unique_lines.append(line)
                        if unique_lines:
                            author_info["author_name"] = unique_lines[0]
                    else:
                        # Fallback to full text if aria-hidden not found
                        author_info["author_name"] = self._extract_text_safe(name_link)
                    break

            # Extract author headline
            headline_selectors = [
                ".update-components-actor__description",
                "span.update-components-actor__description",
                ".feed-shared-actor__description",
            ]

            for selector in headline_selectors:
                headline_elem = self._find_element_in_parent(
                    actor_container, By.CSS_SELECTOR, selector
                )
                if headline_elem:
                    # Try to get from aria-hidden span first to avoid duplicates
                    headline_aria = self._find_element_in_parent(
                        headline_elem, By.CSS_SELECTOR, 'span[aria-hidden="true"]'
                    )
                    if headline_aria:
                        headline_text = self._extract_text_safe(headline_aria)
                    else:
                        headline_text = self._extract_text_safe(headline_elem)

                    if headline_text:
                        # Clean up duplicates
                        headline_lines = [
                            line.strip() for line in headline_text.split("\n") if line.strip()
                        ]
                        # Get unique lines preserving order
                        seen = set()
                        unique_lines = []
                        for line in headline_lines:
                            if line not in seen:
                                seen.add(line)
                                unique_lines.append(line)
                        if unique_lines:
                            author_info["author_headline"] = unique_lines[0]
                        break

            # Extract connection degree (e.g., "1st", "2nd", "3rd+")
            supplementary_selectors = [
                ".update-components-actor__supplementary-actor-info",
                "span.update-components-actor__supplementary-actor-info",
            ]

            for selector in supplementary_selectors:
                supplementary_elem = self._find_element_in_parent(
                    actor_container, By.CSS_SELECTOR, selector
                )
                if supplementary_elem:
                    supplementary_text = self._extract_text_safe(supplementary_elem)
                    # Extract connection degree from text like "• 1st" or "• 3rd+"
                    if "1st" in supplementary_text:
                        author_info["connection_degree"] = "1st"
                    elif "2nd" in supplementary_text:
                        author_info["connection_degree"] = "2nd"
                    elif "3rd" in supplementary_text:
                        author_info["connection_degree"] = "3rd+"
                    break

        except Exception as e:
            self.log_action("WARNING", f"Error extracting author info: {e!s}")

        return author_info

    def _extract_text_as_markdown(self, element: WebElement) -> str:
        """Extract text from element preserving links in markdown format.

        Converts HTML like:
        'Text <a href="url">link</a> more text'
        to:
        'Text [link](url) more text'
        """
        try:
            # Get the innerHTML and parse it to preserve structure
            inner_html = element.get_attribute("innerHTML")
            if not inner_html:
                return self._extract_text_safe(element)

            # Use BeautifulSoup-like parsing with simple regex and string operations
            import re

            # Replace <br> and <br/> tags with newlines
            text = re.sub(r"<br\s*/?>", "\n", inner_html, flags=re.IGNORECASE)

            # Process links: <a href="url">text</a> -> [text](url)
            # Match anchor tags and extract href and text
            link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'

            def replace_link(match):
                url = match.group(1)
                # Get inner content and strip any nested HTML tags
                inner_content = match.group(2)
                # Remove any HTML tags from inner content
                link_text = re.sub(r"<[^>]+>", "", inner_content).strip()

                # Skip if it's empty
                if not link_text:
                    return ""

                # Convert relative URLs to absolute URLs
                if url.startswith("/"):
                    url = f"https://www.linkedin.com{url}"
                elif not url.startswith("http"):
                    url = f"https://www.linkedin.com/{url}"

                return f"[{link_text}]({url})"

            text = re.sub(link_pattern, replace_link, text, flags=re.IGNORECASE | re.DOTALL)

            # Remove any remaining HTML tags
            text = re.sub(r"<[^>]+>", "", text)

            # Decode HTML entities
            import html

            text = html.unescape(text)

            # Clean up extra whitespace while preserving intentional line breaks
            lines = text.split("\n")
            cleaned_lines = []
            for line in lines:
                cleaned_line = " ".join(line.split())  # Normalize spaces within line
                if cleaned_line:  # Only keep non-empty lines
                    cleaned_lines.append(cleaned_line)

            text = "\n".join(cleaned_lines)

            return text.strip()

        except Exception as e:
            self.log_action("DEBUG", f"Error extracting text as markdown: {e!s}")
            # Fallback to plain text extraction
            return self._extract_text_safe(element)

    def _parse_relative_time_to_utc(self, relative_time: str) -> str:
        """Convert relative time string (e.g., '2h', '4d') to UTC timestamp."""
        try:
            relative_time = relative_time.strip().lower()
            now = datetime.now(timezone.utc)

            # Parse the number and unit
            if "mo" in relative_time:
                # Months (e.g., "2mo")
                months = int(relative_time.replace("mo", "").strip())
                # Approximate: 1 month = 30 days
                post_datetime = now - timedelta(days=months * 30)
            elif "w" in relative_time:
                # Weeks (e.g., "2w")
                weeks = int(relative_time.replace("w", "").strip())
                post_datetime = now - timedelta(weeks=weeks)
            elif "d" in relative_time:
                # Days (e.g., "4d")
                days = int(relative_time.replace("d", "").strip())
                post_datetime = now - timedelta(days=days)
            elif "h" in relative_time:
                # Hours (e.g., "2h")
                hours = int(relative_time.replace("h", "").strip())
                post_datetime = now - timedelta(hours=hours)
            elif "m" in relative_time:
                # Minutes (e.g., "30m")
                minutes = int(relative_time.replace("m", "").strip())
                post_datetime = now - timedelta(minutes=minutes)
            elif "s" in relative_time:
                # Seconds (e.g., "45s")
                seconds = int(relative_time.replace("s", "").strip())
                post_datetime = now - timedelta(seconds=seconds)
            else:
                # If we can't parse, return the original string
                return relative_time

            # Return ISO 8601 format timestamp
            return post_datetime.isoformat()
        except Exception:
            # If parsing fails, return the original string
            return relative_time

    def _extract_post_content(self, container: WebElement) -> dict[str, Any]:
        """Extract post text, hashtags, external links, and posting time.

        Note: Only external domain links are stored (LinkedIn redirect URLs and non-LinkedIn domains).
        Internal LinkedIn links (profiles, companies, posts) are excluded.
        """
        content_info = {
            "post_text": "N/A",
            "hashtags": [],
            "links": [],
            "post_time": "N/A",
        }

        try:
            # Extract post text
            text_selectors = [
                ".update-components-text",
                ".feed-shared-update-v2__description",
                ".feed-shared-text",
                "div.update-components-update-v2__commentary",
            ]

            post_content_elem = None
            for selector in text_selectors:
                text_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if text_elem:
                    # Extract text as markdown to preserve links
                    post_text = self._extract_text_as_markdown(text_elem)
                    if post_text and post_text != "…more":
                        content_info["post_text"] = post_text
                        post_content_elem = text_elem
                        break

            # Extract hashtags from the text element
            hashtag_links = container.find_elements(
                By.CSS_SELECTOR, "a[href*='/search/results/all/?keywords=%23']"
            )
            hashtags = []
            for link in hashtag_links:
                hashtag_text = self._extract_text_safe(link)
                if hashtag_text and hashtag_text.startswith("#"):
                    hashtags.append(hashtag_text)

            if hashtags:
                content_info["hashtags"] = hashtags

            # Extract links from the post content (external domains only)
            if post_content_elem:
                links = []
                link_elements = post_content_elem.find_elements(By.TAG_NAME, "a")
                for link_elem in link_elements:
                    href = self._extract_attribute_safe(link_elem, "href")

                    # Skip hashtag links (already extracted separately)
                    if not href or "/search/results/all/?keywords=%23" in href:
                        continue

                    # Keep LinkedIn redirect URLs (these point to external sites)
                    if "linkedin.com/redir/" in href:
                        links.append(href)
                        continue

                    # For other links, only keep external domains (not linkedin.com)
                    if href.startswith("http"):
                        # Parse the URL to check domain
                        parsed = urllib.parse.urlparse(href)
                        # Skip if it's a LinkedIn domain link
                        if "linkedin.com" not in parsed.netloc:
                            links.append(href)

                if links:
                    content_info["links"] = links

            # Extract post time
            time_selectors = [
                ".update-components-actor__sub-description",
                "span.update-components-actor__sub-description",
                ".feed-shared-actor__sub-description",
            ]

            for selector in time_selectors:
                time_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if time_elem:
                    time_text = self._extract_text_safe(time_elem)
                    if time_text:
                        # Extract time from text like "4d •" or "2h •"
                        time_parts = time_text.split("•")
                        if time_parts:
                            relative_time = time_parts[0].strip()
                            # Convert to UTC timestamp
                            content_info["post_time"] = self._parse_relative_time_to_utc(
                                relative_time
                            )
                            break

        except Exception as e:
            self.log_action("WARNING", f"Error extracting post content: {e!s}")

        return content_info

    def _extract_engagement_metrics(self, container: WebElement) -> dict[str, int]:
        """Extract likes, comments, and reposts counts."""
        metrics = {
            "likes_count": 0,
            "comments_count": 0,
            "reposts_count": 0,
        }

        try:
            # Extract likes count
            likes_selectors = [
                "button[aria-label*='reactions']",
                "button[data-reaction-details]",
                ".social-details-social-counts__reactions",
            ]

            for selector in likes_selectors:
                likes_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if likes_elem:
                    likes_text = self._extract_text_safe(likes_elem)
                    if not likes_text:
                        # Try aria-label
                        likes_text = self._extract_attribute_safe(likes_elem, "aria-label")

                    # Extract number from text like "12 reactions" or "12"
                    if likes_text:
                        import re

                        numbers = re.findall(r"\d+", likes_text)
                        if numbers:
                            metrics["likes_count"] = int(numbers[0])
                            break

            # Extract comments count
            comment_selectors = [
                "button[aria-label*='comment']",
                "li.social-details-social-counts__comments",
                "button.comment-button",
            ]

            for selector in comment_selectors:
                comment_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if comment_elem:
                    comment_text = self._extract_text_safe(comment_elem)
                    if not comment_text:
                        comment_text = self._extract_attribute_safe(comment_elem, "aria-label")

                    if comment_text:
                        import re

                        numbers = re.findall(r"\d+", comment_text)
                        if numbers:
                            metrics["comments_count"] = int(numbers[0])
                            break

            # Extract reposts count
            repost_selectors = [
                "button[aria-label*='repost']",
                "li.social-details-social-counts__item--reposts",
            ]

            for selector in repost_selectors:
                repost_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if repost_elem:
                    repost_text = self._extract_text_safe(repost_elem)
                    if not repost_text:
                        repost_text = self._extract_attribute_safe(repost_elem, "aria-label")

                    if repost_text:
                        import re

                        numbers = re.findall(r"\d+", repost_text)
                        if numbers:
                            metrics["reposts_count"] = int(numbers[0])
                            break

        except Exception as e:
            self.log_action("WARNING", f"Error extracting engagement metrics: {e!s}")

        return metrics

    def _extract_post_url(self, container: WebElement) -> str | None:
        """Extract the URL to the post."""
        try:
            # Look for post link in various places
            link_selectors = [
                "a[href*='/feed/update/']",
                "a[href*='/posts/']",
                ".update-components-actor__sub-description a",
            ]

            for selector in link_selectors:
                link_elem = self._find_element_in_parent(container, By.CSS_SELECTOR, selector)
                if link_elem:
                    href = self._extract_attribute_safe(link_elem, "href")
                    if href and ("/feed/update/" in href or "/posts/" in href):
                        return href.split("?")[0]  # Remove query parameters

        except Exception as e:
            self.log_action("WARNING", f"Error extracting post URL: {e!s}")

        return None

    def _extract_post_media(self, container: WebElement) -> list[str]:
        """Extract all media URLs (images and videos) from post."""
        media_urls = []

        try:
            # Extract all images
            image_selectors = [
                ".update-components-image img",
                "img.update-components-image__image",
                "img[alt*='image']",
                ".feed-shared-image img",
                ".feed-shared-image__image",
            ]

            for selector in image_selectors:
                try:
                    img_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for img_elem in img_elements:
                        src = self._extract_attribute_safe(img_elem, "src")
                        if src and src.startswith("http") and src not in media_urls:
                            media_urls.append(src)
                except Exception as e:
                    self.log_action(
                        "DEBUG", f"Could not extract images with selector {selector}: {e!s}"
                    )
                    continue

            # Extract video URLs
            video_selectors = [
                "video source",
                "video[src]",
                ".feed-shared-video video",
                ".update-components-video video",
            ]

            for selector in video_selectors:
                try:
                    video_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for video_elem in video_elements:
                        # Try to get src from source element or video element
                        src = self._extract_attribute_safe(video_elem, "src")
                        if not src:
                            # Try to get from data attributes
                            src = self._extract_attribute_safe(video_elem, "data-src")

                        if src and src.startswith("http") and src not in media_urls:
                            media_urls.append(src)
                except Exception as e:
                    self.log_action(
                        "DEBUG", f"Could not extract videos with selector {selector}: {e!s}"
                    )
                    continue

            # Also check for video poster images
            video_poster_selectors = [
                "video[poster]",
            ]

            for selector in video_poster_selectors:
                try:
                    video_elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for video_elem in video_elements:
                        poster = self._extract_attribute_safe(video_elem, "poster")
                        if poster and poster.startswith("http") and poster not in media_urls:
                            media_urls.append(poster)
                except Exception as e:
                    self.log_action(
                        "DEBUG", f"Could not extract video posters with selector {selector}: {e!s}"
                    )
                    continue

        except Exception as e:
            self.log_action("WARNING", f"Error extracting post media: {e!s}")

        return media_urls

    def _load_more_comments(self, container: WebElement, max_comments: int) -> None:
        """Load more comments by clicking 'Load more comments' buttons."""
        try:
            load_more_attempts = 0
            max_load_attempts = (max_comments // 5) + 2  # Estimate attempts needed
            previous_count = 0

            while load_more_attempts < max_load_attempts:
                # Count current comments
                current_comments = container.find_elements(
                    By.CSS_SELECTOR, "article.comments-comment-entity"
                )
                current_count = len(current_comments)

                # If we have enough comments or no new comments loaded, stop
                if current_count >= max_comments or (
                    current_count == previous_count and load_more_attempts > 0
                ):
                    self.log_action(
                        "DEBUG", f"Loaded {current_count} comments, stopping load more attempts"
                    )
                    break

                previous_count = current_count

                # Try to find and click "Load more comments" or similar buttons
                load_more_button_selectors = [
                    "button[aria-label*='Load more comments']",
                    "button[aria-label*='Load previous']",
                    "button.comments-comments-list__load-more-comments-button",
                    "button.comments-replies-list__replies-button",
                ]

                button_clicked = False
                for selector in load_more_button_selectors:
                    try:
                        load_buttons = container.find_elements(By.CSS_SELECTOR, selector)
                        for load_button in load_buttons:
                            try:
                                # Check if button is visible and clickable
                                if load_button.is_displayed():
                                    load_button.click()
                                    button_clicked = True
                                    self.log_action("DEBUG", "Clicked load more comments button")
                                    # Wait for new comments to load
                                    self.human_behavior.delay(1.0, 2.0)
                                    break
                            except Exception as e:
                                self.log_action("DEBUG", f"Could not click load more button: {e!s}")
                                continue

                        if button_clicked:
                            break
                    except Exception as e:
                        self.log_action(
                            "DEBUG",
                            f"Could not find load more button with selector {selector}: {e!s}",
                        )
                        continue

                # If no button was clicked, we're done
                if not button_clicked:
                    self.log_action("DEBUG", "No more 'load more comments' buttons found")
                    break

                load_more_attempts += 1

        except Exception as e:
            self.log_action("DEBUG", f"Error loading more comments: {e!s}")

    def open_link(self, url: str) -> dict[str, Any] | None:
        """
        Open a LinkedIn post URL and extract its content.

        Args:
            url: LinkedIn post URL (e.g., https://linkedin.com/feed/update/urn:li:activity:...)

        Returns:
            Dictionary containing post data (same structure as search_posts), or None if failed
        """
        try:
            self.log_action("INFO", f"Opening LinkedIn URL: {url}")

            if not self.navigate_to_url(url):
                self.log_action("ERROR", f"Failed to navigate to URL: {url}")
                return None

            # Wait for page load
            self.human_behavior.delay(2.0, 4.0)

            # Find the first post container
            post_containers = self._find_post_containers()

            if not post_containers:
                self.log_action("WARNING", "No post container found on page")
                return None

            # Extract data from the first post
            post_data = self._extract_post_data(post_containers[0])

            # Set post_url if not already set
            if post_data.get("post_url") == "N/A":
                post_data["post_url"] = url.split("?")[0]

        except Exception as e:
            self.log_action("ERROR", f"Failed to open link: {e!s}")
            return None
        else:
            self.log_action("SUCCESS", f"Extracted post from URL: {url}")
            return post_data

    def _extract_post_comments(
        self, container: WebElement, max_comments: int = 10
    ) -> list[dict[str, Any]]:
        """Extract comments from a post.

        Args:
            container: Post container WebElement
            max_comments: Maximum number of comments to extract (default: 10)

        Returns:
            List of comment dictionaries with keys:
            - author_name
            - author_profile_url
            - comment_text (markdown format with links)
            - comment_time (ISO 8601 UTC timestamp)
            - reactions_count
        """
        comments = []

        try:
            # First, try to click on the comments button/count to expand comments section
            comments_button_selectors = [
                "button[aria-label*='comment'] span",
                "li.social-details-social-counts__comments button span",
                "button.comment-button",
            ]

            for selector in comments_button_selectors:
                try:
                    comments_button = self._find_element_in_parent(
                        container, By.CSS_SELECTOR, selector
                    )
                    if comments_button:
                        # Check if there are any comments to expand
                        button_text = self._extract_text_safe(comments_button)
                        aria_label = self._extract_attribute_safe(comments_button, "aria-label")

                        # Only click if there are comments (text contains numbers)
                        import re

                        if button_text or aria_label:
                            text_to_check = button_text or aria_label
                            numbers = re.findall(r"\d+", text_to_check)
                            if numbers and int(numbers[0]) > 0:
                                try:
                                    comments_button.click()
                                    # Wait for comments to load
                                    self.human_behavior.delay(1.0, 2.0)
                                    self.log_action("DEBUG", "Clicked comments button to expand")
                                    break
                                except Exception as e:
                                    self.log_action(
                                        "DEBUG", f"Could not click comments button: {e!s}"
                                    )
                except Exception as e:
                    self.log_action(
                        "DEBUG", f"Could not find comments button with selector {selector}: {e!s}"
                    )
                    continue

            # Load more comments by clicking "Load more comments" buttons
            self._load_more_comments(container, max_comments)

            # Find all comment entities (whether expanded or already visible)
            comment_entities = container.find_elements(
                By.CSS_SELECTOR, "article.comments-comment-entity"
            )

            for comment_elem in comment_entities[:max_comments]:
                try:
                    comment_data = {
                        "author_name": "N/A",
                        "author_profile_url": "N/A",
                        "comment_text": "N/A",
                        "comment_time": "N/A",
                        "reactions_count": 0,
                    }

                    # Extract author name
                    name_elem = self._find_element_in_parent(
                        comment_elem,
                        By.CSS_SELECTOR,
                        "span.comments-comment-meta__description-title",
                    )
                    if name_elem:
                        comment_data["author_name"] = self._extract_text_safe(name_elem)

                    # Extract author profile URL
                    profile_link = self._find_element_in_parent(
                        comment_elem,
                        By.CSS_SELECTOR,
                        "a.comments-comment-meta__description-container",
                    )
                    if profile_link:
                        profile_url = self._extract_attribute_safe(profile_link, "href")
                        if profile_url:
                            comment_data["author_profile_url"] = profile_url.split("?")[0]

                    # Extract comment text
                    text_selectors = [
                        ".comments-comment-item__main-content",
                        ".update-components-text",
                        ".comments-comment-item-content",
                    ]

                    for selector in text_selectors:
                        text_elem = self._find_element_in_parent(
                            comment_elem, By.CSS_SELECTOR, selector
                        )
                        if text_elem:
                            # Extract text as markdown to preserve links
                            comment_text = self._extract_text_as_markdown(text_elem)
                            if comment_text:
                                comment_data["comment_text"] = comment_text
                                break

                    # Extract comment time
                    time_elem = self._find_element_in_parent(
                        comment_elem, By.CSS_SELECTOR, "time.comments-comment-meta__data"
                    )
                    if time_elem:
                        relative_time = self._extract_text_safe(time_elem)
                        # Convert to UTC timestamp
                        comment_data["comment_time"] = self._parse_relative_time_to_utc(
                            relative_time
                        )

                    # Extract reactions count
                    reactions_button = self._find_element_in_parent(
                        comment_elem,
                        By.CSS_SELECTOR,
                        "button.comments-comment-social-bar__reactions-count--cr",
                    )
                    if reactions_button:
                        aria_label = self._extract_attribute_safe(reactions_button, "aria-label")
                        if aria_label:
                            # Extract number from aria-label like "5 Reactions on Vipin Gautam's comment"
                            import re

                            numbers = re.findall(r"^\d+", aria_label)
                            if numbers:
                                comment_data["reactions_count"] = int(numbers[0])

                    # Only add if we got meaningful data
                    if comment_data["author_name"] != "N/A":
                        comments.append(comment_data)

                except Exception as e:
                    self.log_action("DEBUG", f"Could not extract comment: {e!s}")
                    continue

        except Exception as e:
            self.log_action("WARNING", f"Error extracting post comments: {e!s}")

        return comments
