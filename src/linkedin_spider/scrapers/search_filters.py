import json
import logging
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".linkedin_spider_profiles"

CONNECTION_NETWORK_MAP = {
    "1": "F",
    "1st": "F",
    "first": "F",
    "f": "F",
    "2": "S",
    "2nd": "S",
    "second": "S",
    "s": "S",
    "3": "O",
    "3rd": "O",
    "3rd+": "O",
    "third": "O",
    "o": "O",
}


@dataclass(frozen=True)
class TypeaheadFacet:
    """A search facet resolved by opening a pill, typing, and picking a suggestion."""

    key: str
    pill_aria_prefix: str
    input_placeholder: str
    url_param: str
    cache_file: str


TYPEAHEAD_FACETS: dict[str, TypeaheadFacet] = {
    "location": TypeaheadFacet(
        key="location",
        pill_aria_prefix="Filter by Locations",
        input_placeholder="Add a location",
        url_param="geoUrn",
        cache_file="geo_urn_cache.json",
    ),
    "current_company": TypeaheadFacet(
        key="current_company",
        pill_aria_prefix="Filter by Current companies",
        input_placeholder="Add a company",
        url_param="currentCompany",
        cache_file="current_company_cache.json",
    ),
}


class SearchFilterHandler:
    def __init__(self, driver: Any, wait: Any, human_behavior: Any) -> None:
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.current_filters: dict[str, Any] = {}
        self._caches: dict[str, dict[str, str]] = {}

    def _load_cache(self, filename: str) -> dict[str, str]:
        if filename in self._caches:
            return self._caches[filename]
        path = CACHE_DIR / filename
        try:
            self._caches[filename] = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            self._caches[filename] = {}
        return self._caches[filename]

    def _save_cache(self, filename: str) -> None:
        if filename not in self._caches:
            return
        path = CACHE_DIR / filename
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self._caches[filename], indent=2, sort_keys=True))
        except OSError:
            logger.warning("Could not persist cache to %s", path)

    def _build_search_url(self, query: str, extra_params: dict[str, str]) -> str:
        params = {"keywords": query}
        if extra_params:
            params["origin"] = "FACETED_SEARCH"
            params.update(extra_params)
        return "https://www.linkedin.com/search/results/people/?" + urllib.parse.urlencode(params)

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
        applied_filters: dict[str, Any] = {}
        url_params: dict[str, str] = {}

        # Resolve cache-hit fast-paths so we can navigate once with all params
        facet_values = {"location": location, "current_company": current_company}
        facets_needing_resolution: list[tuple[TypeaheadFacet, str]] = []

        for facet_key, value in facet_values.items():
            if not value:
                continue
            facet = TYPEAHEAD_FACETS[facet_key]
            cache = self._load_cache(facet.cache_file)
            cached_urn = cache.get(value.lower())
            if cached_urn:
                logger.info("Using cached %s for '%s': %s", facet.url_param, value, cached_urn)
                url_params[facet.url_param] = f'["{cached_urn}"]'
                applied_filters[facet_key] = {
                    "query": value,
                    "urn": cached_urn,
                    "cached": True,
                }
            else:
                facets_needing_resolution.append((facet, value))

        if connections:
            network_code = CONNECTION_NETWORK_MAP.get(connections.lower())
            if network_code:
                url_params["network"] = f'["{network_code}"]'
                applied_filters["connections"] = {
                    "value": connections,
                    "network": network_code,
                }
            else:
                logger.warning("Unknown connections value '%s'", connections)

        self.driver.get(self._build_search_url(query, url_params))
        self.human_behavior.delay(2, 4)

        # Resolve uncached typeahead facets to discover their URNs. Each click flow
        # rewrites the URL with just that facet's param — so we drop everything else
        # and do a final consolidated navigate once all URNs are known.
        for facet, value in facets_needing_resolution:
            resolved = self._resolve_typeahead_facet(facet, value)
            if not resolved:
                continue
            applied_filters[facet.key] = resolved
            cache = self._load_cache(facet.cache_file)
            cache[value.lower()] = resolved["urn"]
            self._save_cache(facet.cache_file)
            url_params[facet.url_param] = f'["{resolved["urn"]}"]'

        if facets_needing_resolution and len(url_params) > 1:
            # We applied multiple filters but the last click flow only kept one in the URL.
            # Navigate once more with all params merged.
            self.driver.get(self._build_search_url(query, url_params))
            self.human_behavior.delay(2, 4)

        self.current_filters = applied_filters
        return str(self.driver.current_url)

    def _resolve_typeahead_facet(self, facet: TypeaheadFacet, query: str) -> dict[str, Any] | None:
        try:
            pill = self._find_pill_button(facet.pill_aria_prefix)
            if not pill:
                logger.warning("%s pill not found", facet.pill_aria_prefix)
                return None
            self.driver.execute_script("arguments[0].click();", pill)
            self.human_behavior.delay(1, 2)

            input_el = self._find_visible_input_by_placeholder(facet.input_placeholder)
            if not input_el:
                logger.warning("Input '%s' not found", facet.input_placeholder)
                return None
            input_el.click()
            input_el.send_keys(query)
            self.human_behavior.delay(1, 2)

            suggestion = self._wait_for_first_matching_option(query)
            if not suggestion:
                logger.warning("No %s suggestion matched '%s'", facet.key, query)
                return None
            selected_text = (suggestion.text or "").strip().split("\n")[0]
            self.driver.execute_script("arguments[0].click();", suggestion)
            self.human_behavior.delay(0.5, 1.5)

            show_results = self._find_popover_show_results()
            if not show_results:
                logger.warning("Show results not found for %s", facet.key)
                return None
            self.driver.execute_script("arguments[0].click();", show_results)
            self.human_behavior.delay(3, 5)

            urn = self._extract_url_param_id(facet.url_param)
            if not urn:
                logger.warning("Filter applied but %s missing from URL", facet.url_param)
                return None
            return {  # noqa: TRY300 - success path among many early-return None guards
                "query": query,
                "selected": selected_text,
                "urn": urn,
                "cached": False,
            }
        except Exception:
            logger.exception("Error resolving facet '%s'", facet.key)
            return None

    def _find_pill_button(self, aria_label_prefix: str) -> WebElement | None:
        """Find a filter-bar pill by its aria-label. Pills are <div> elements on current LinkedIn."""
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, f"[aria-label^='{aria_label_prefix}']"
            )
            for el in elements:
                if el.is_displayed():
                    return cast("WebElement", el)
        except Exception:
            return None
        return None

    def _find_visible_input_by_placeholder(self, placeholder: str) -> WebElement | None:
        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR, f"input[placeholder='{placeholder}']"
            )
            for inp in inputs:
                if inp.is_displayed():
                    return cast("WebElement", inp)
        except Exception:
            return None
        return None

    def _wait_for_first_matching_option(self, query: str, timeout: int = 5) -> WebElement | None:
        query_lower = query.lower()

        def find_match(_driver: Any) -> WebElement | None:
            options = _driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in options:
                if not opt.is_displayed():
                    continue
                text = (opt.text or "").strip().lower()
                if text.startswith(query_lower) or query_lower in text:
                    return cast("WebElement", opt)
            return None

        try:
            return WebDriverWait(self.driver, timeout).until(find_match)
        except TimeoutException:
            return None

    def _find_popover_show_results(self) -> WebElement | None:
        try:
            candidates = self.driver.find_elements(
                By.XPATH,
                "//*[self::a or self::button][normalize-space(.)='Show results']",
            )
            visible = [c for c in candidates if c.is_displayed()]
            if not visible:
                return None
            # The popover's Show results is the last-rendered visible one (the side
            # complementary panel renders earlier in the DOM).
            return cast("WebElement", visible[-1])
        except Exception:
            return None

    def _extract_url_param_id(self, param_name: str) -> str | None:
        try:
            current = self.driver.current_url
            params = urllib.parse.parse_qs(urllib.parse.urlparse(current).query)
            raw = params.get(param_name, [None])[0]
            if not raw:
                return None
            match = re.search(r"\d+", raw)
            return match.group(0) if match else None
        except Exception:
            return None

    def get_applied_filters(self) -> dict[str, Any]:
        return self.current_filters

    def reset_filters(self) -> bool:
        """Clear in-memory applied filters. Caller is responsible for navigating away."""
        self.current_filters = {}
        return True
