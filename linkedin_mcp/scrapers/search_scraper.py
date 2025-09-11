import time
import random
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .search_filters import SearchFilters, DynamicFilterScraper, build_search_url

class SearchScraper:
    def __init__(self, driver, wait, human_behavior, tracking_handler):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.tracking_handler = tracking_handler
        self.dynamic_filter_scraper = DynamicFilterScraper(driver, wait, human_behavior)

    def search_profiles(self, query, max_results=10, filters=None, save_html_path="search_results.html"):
        print(f"Searching for: '{query}'")
        
        if filters and not filters.is_empty():
            print(f"Applying dynamic filters: {filters}")
            search_url = filters.apply_with_scraper(self.dynamic_filter_scraper, query)
            print(f"Search URL with filters: {search_url}")
        else:
            search_url = build_search_url(query, None)
            self.driver.get(search_url)

        self.human_behavior.human_delay(1, 3)
        self.human_behavior.simulate_reading_behavior(1, 2)

        profile_data = []
        page_number = 1
        max_pages = 10

        try:
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-view-name='people-search-result']")
            ))

            html = self.driver.page_source
            with open(save_html_path, "w", encoding="utf-8") as f:
                f.write(html)

            while len(profile_data) < max_results and page_number <= max_pages:
                print(f"Scraping page {page_number}...")
                
                scroll_attempts = 0
                max_scroll_attempts = 3
                
                while scroll_attempts < max_scroll_attempts:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='people-search-result']")
                    processed_containers = self.tracking_handler.handle_search_result_tracking(containers)

                    for container in processed_containers:
                        if len(profile_data) >= max_results:
                            break
                            
                        data = {}
                        try:
                            name_el = container.find_element(By.CSS_SELECTOR,
                                                             'a[data-view-name="search-result-lockup-title"]')
                            data["name"] = name_el.text.strip()
                            href = name_el.get_attribute("href")
                            data["profile_url"] = href if href and 'linkedin.com/in/' in href else "N/A"
                        except:
                            data["name"] = "N/A"
                            data["profile_url"] = "N/A"

                        try:
                            headline_el = container.find_elements(By.CSS_SELECTOR, "p")
                            data["headline"] = headline_el[1].text.strip() if len(headline_el) > 1 else "N/A"
                        except:
                            data["headline"] = "N/A"

                        try:
                            location_el = container.find_elements(By.CSS_SELECTOR, "p")
                            data["location"] = location_el[2].text.strip() if len(location_el) > 2 else "N/A"
                        except:
                            data["location"] = "N/A"

                        try:
                            img_el = container.find_element(By.CSS_SELECTOR, "img")
                            data["image_url"] = img_el.get_attribute("src")
                        except:
                            data["image_url"] = "N/A"

                        if data not in profile_data:
                            profile_data.append(data)

                    if len(profile_data) >= max_results:
                        break
                        
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    self.human_behavior.human_scroll("down", random.randint(300, 600))
                    self.human_behavior.human_delay(1, 2)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    scroll_attempts += 1
                
                if len(profile_data) >= max_results:
                    break
                    
                if not self._handle_pagination():
                    break
                    
                page_number += 1
                self.human_behavior.human_delay(2, 4)

            print(f"[SUCCESS] Extracted {len(profile_data)} profiles from {page_number} pages")
            return profile_data

        except Exception as e:
            print(f"[ERROR] Error during search: {str(e)}")
            return []

    def extract_headless_data(self):
        profiles_data = []
        try:
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='people-search-result']")
            processed_containers = self.tracking_handler.handle_search_result_tracking(containers)

            for container in processed_containers:
                profile_data = {}

                try:
                    name_el = container.find_element(By.CSS_SELECTOR, 'a[data-view-name="search-result-lockup-title"]')
                    profile_data['name'] = name_el.text.strip() if name_el.text.strip() else "Anonymous"
                    href = name_el.get_attribute("href")
                    profile_data['profile_url'] = href if href and 'linkedin.com/in/' in href else "N/A"
                except:
                    profile_data['name'] = "Anonymous"
                    profile_data['profile_url'] = "N/A"

                try:
                    headline_el = container.find_elements(By.CSS_SELECTOR, "p")
                    profile_data['headline'] = headline_el[1].text.strip() if len(headline_el) > 1 else "N/A"
                except:
                    profile_data['headline'] = "N/A"

                try:
                    location_el = container.find_elements(By.CSS_SELECTOR, "p")
                    profile_data['location'] = location_el[2].text.strip() if len(location_el) > 2 else "N/A"
                except:
                    profile_data['location'] = "N/A"


                profile_data['about'] = "N/A"
                profile_data['experience'] = []

                if profile_data['name'] != "Anonymous" or profile_data['headline'] != "N/A":
                    profiles_data.append(profile_data)

            return profiles_data
        except Exception as e:
            print(f"Error extracting headless data: {str(e)}")
            return []
    
    def _handle_pagination(self):
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='pagination-control-next-btn']")
            if next_btn.is_enabled() and next_btn.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                self.human_behavior.human_delay(0.5, 1.5)
                next_btn.click()
                self.human_behavior.human_delay(2, 4)
                
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-view-name='people-search-result']")
                ))
                return True
        except:
            pass
        return False
