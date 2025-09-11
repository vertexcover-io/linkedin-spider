import time
import re
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait

class DynamicFilterScraper:
    def __init__(self, driver, wait, human_behavior):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.current_filters = {}
    
    def search_and_apply_filters(self, query, location=None, industry=None, current_company=None, connections=None):
        base_search_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(query)}"
        self.driver.get(base_search_url)
        
        self.human_behavior.human_delay(2, 4)
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")))
        
        applied_filters = {}
        
        if location:
            location_filter = self._apply_location_filter(location)
            if location_filter:
                applied_filters['location'] = location_filter
                print(self._click_show_results())
        
        if industry:
            industry_filter = self._apply_industry_filter(industry)
            if industry_filter:
                applied_filters['industry'] = industry_filter
                self._click_show_results()
        
        if current_company:
            company_filter = self._apply_company_filter(current_company)
            if company_filter:
                applied_filters['current_company'] = company_filter
                self._click_show_results()
        
        if connections:
            connection_filter = self._apply_connection_filter(connections)
            if connection_filter:
                applied_filters['connections'] = connection_filter
        
        self.current_filters = applied_filters
        return self.driver.current_url
    
    def _apply_location_filter(self, location_query):
        try:
            location_button = self._find_filter_button_by_text("India")
            if not location_button:
                location_button = self._find_filter_button_by_text("Location")
                
            if location_button:
                self.driver.execute_script("arguments[0].click();", location_button)
                self.human_behavior.human_delay(1, 2)
                
                dropdown_opened = self._wait_for_dropdown()
                if dropdown_opened:
                    return self._search_and_select_filter_option(location_query, "location")
            
            return None
        except Exception as e:
            print(f"Error applying location filter: {str(e)}")
            return None
    
    def _apply_industry_filter(self, industry_query):
        try:
            all_filters_btn = self._find_button_by_text("All filters")
            if all_filters_btn:
                self.driver.execute_script("arguments[0].click();", all_filters_btn)
                self.human_behavior.human_delay(1, 3)
                
                industry_section = self._find_filter_modal_section("Industry")
                if industry_section:
                    return self._search_in_modal_section(industry_section, industry_query, "industry")
            
            return None
        except Exception as e:
            print(f"Error applying industry filter: {str(e)}")
            return None
    
    def _apply_company_filter(self, company_query):
        try:
            company_button = self._find_filter_button_by_text("Current companies")
            if company_button:
                self.driver.execute_script("arguments[0].click();", company_button)
                self.human_behavior.human_delay(1, 2)
                
                dropdown_opened = self._wait_for_dropdown()
                if dropdown_opened:
                    return self._search_and_select_filter_option(company_query, "company")
            
            return None
        except Exception as e:
            print(f"Error applying company filter: {str(e)}")
            return None
    
    def _apply_connection_filter(self, connection_level):
        try:
            connection_mapping = {
                '1st': '1st', 'first': '1st', '1': '1st',
                '2nd': '2nd', 'second': '2nd', '2': '2nd', 
                '3rd': '3rd+', 'third': '3rd+', '3': '3rd+'
            }
            
            target_connection = connection_mapping.get(connection_level.lower())
            if not target_connection:
                return None
                
            connection_button = self._find_filter_button_by_text(target_connection)
            if connection_button:
                self.driver.execute_script("arguments[0].click();", connection_button)
                self.human_behavior.human_delay(1, 2)
                return {'level': target_connection, 'param': self._extract_connection_param()}
            
            return None
        except Exception as e:
            print(f"Error applying connection filter: {str(e)}")
            return None
    
    def _find_filter_button_by_text(self, text):
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")
            for button in buttons:
                if text.lower() in button.text.lower():
                    return button
            return None
        except:
            return None
    
    def _find_button_by_text(self, text):
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if text.lower() in button.text.lower():
                    return button
            return None
        except:
            return None
    
    def _wait_for_dropdown(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Add'], input[type='text']"))
            )
            return True
        except TimeoutException:
            return False
    
    def _search_and_select_filter_option(self, query, filter_type):
        try:
            search_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-menu-tyah']")))            
            search_input.clear()
            search_input.send_keys(query)
            self.human_behavior.human_delay(1, 2)
            
            suggestions = self._wait_for_suggestions()
            if suggestions:
                best_match = self._find_best_match(suggestions, query)
                if best_match:
                    self.driver.execute_script("arguments[0].click();", best_match)
                    self.human_behavior.human_delay(1, 2)
                    
                    selected_text = best_match.find_element(By.TAG_NAME, "p").text if best_match.find_elements(By.TAG_NAME, "p") else best_match.text
                    
                    return {
                        'query': query,
                        'selected': selected_text,
                        'param': self._extract_filter_param(filter_type)
                    }
            
            return None
        except Exception as e:
            print(f"Error in search and select: {str(e)}")
            return None
    
    def _wait_for_suggestions(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-menu-item'], [role='checkbox'], [role='option']"))
            )
            return self.driver.find_elements(By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-menu-item'], [role='checkbox'], [role='option']")
        except TimeoutException:
            return []
    
    def _find_best_match(self, suggestions, query):
        query_lower = query.lower()
        best_match = None
        highest_score = 0
        
        for suggestion in suggestions:
            try:
                text_element = suggestion.find_element(By.TAG_NAME, "p") if suggestion.find_elements(By.TAG_NAME, "p") else suggestion
                text = text_element.text.lower()
                if query_lower in text:
                    score = len(query_lower) / len(text) if text else 0
                    if score > highest_score:
                        highest_score = score
                        best_match = suggestion
            except:
                continue
        
        return best_match if best_match else (suggestions[0] if suggestions else None)
    
    def _find_filter_modal_section(self, section_name):
        try:
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h3, h2, legend, .filter-section-title")
            for heading in headings:
                if section_name.lower() in heading.text.lower():
                    return heading.find_element(By.XPATH, "./following-sibling::*[1]")
            return None
        except:
            return None
    
    def _search_in_modal_section(self, section, query, filter_type):
        try:
            search_input = section.find_element(By.CSS_SELECTOR, "input[type='text']")
            search_input.clear()
            search_input.send_keys(query)
            self.human_behavior.human_delay(1, 2)
            
            options = section.find_elements(By.CSS_SELECTOR, "[role='checkbox'], .option-item")
            best_match = self._find_best_match(options, query)
            
            if best_match:
                self.driver.execute_script("arguments[0].click();", best_match)
                self.human_behavior.human_delay(1, 2)
                
                apply_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-control-name='all_filters_apply']")
                if apply_btn:
                    self.driver.execute_script("arguments[0].click();", apply_btn)
                    self.human_behavior.human_delay(2, 3)
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")))
                
                return {
                    'query': query,
                    'selected': best_match.text,
                    'param': self._extract_filter_param(filter_type)
                }
            
            return None
        except Exception as e:
            print(f"Error in modal section search: {str(e)}")
            return None
    
    def _extract_filter_param(self, filter_type):
        current_url = self.driver.current_url
        parsed_url = urllib.parse.urlparse(current_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        param_map = {
            'location': ['geoUrn', 'location'],
            'industry': ['industryUrn', 'industry'], 
            'company': ['currentCompany', 'companyUrn'],
            'connections': ['network', 'connectionDepth']
        }
        
        for param_key in param_map.get(filter_type, []):
            if param_key in params:
                return {param_key: params[param_key][0]}
        
        return {}
    
    def _extract_connection_param(self):
        current_url = self.driver.current_url
        if 'network=' in current_url:
            network_match = re.search(r'network=([^&]+)', current_url)
            if network_match:
                return {'network': network_match.group(1)}
        return {}
    
    def get_applied_filters(self):
        return self.current_filters
    
    def _click_show_results(self):
        try:
            selectors = [
                "[data-view-name='search-filter-top-bar-menu-submit']",
                "button[componentkey*='submit']", 
                "button:contains('Show results')",
                "button[type='button']:last-child"
            ]
            
            for selector in selectors:
                try:
                    if 'contains' in selector:
                        show_results_btn = self.driver.execute_script(
                            "return Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Show results'));"
                        )
                    else:
                        show_results_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    if show_results_btn:
                        self.driver.execute_script("arguments[0].click();", show_results_btn)
                        self.human_behavior.human_delay(2, 4)
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-view-name='search-filter-top-bar-select']")))
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"Error clicking show results: {str(e)}")
            return False
    
    def reset_filters(self):
        try:
            reset_btn = self._find_button_by_text("Reset")
            if reset_btn:
                self.driver.execute_script("arguments[0].click();", reset_btn)
                self.human_behavior.human_delay(1, 2)
                self.current_filters = {}
                return True
            return False
        except:
            return False

class DynamicSearchFilters:
    def __init__(self, location=None, industry=None, current_company=None, connections=None):
        self.location = location
        self.industry = industry  
        self.current_company = current_company
        self.connections = connections
        self.applied_params = {}
    
    def apply_with_scraper(self, scraper, query):
        url = scraper.search_and_apply_filters(
            query=query,
            location=self.location,
            industry=self.industry,
            current_company=self.current_company,
            connections=self.connections
        )
        
        self.applied_params = scraper.get_applied_filters()
        return url
    
    def is_empty(self):
        return not any([self.location, self.industry, self.current_company, self.connections])
    
    def __str__(self):
        filters = []
        if self.location:
            filters.append(f"Location: {self.location}")
        if self.industry:
            filters.append(f"Industry: {self.industry}")
        if self.current_company:
            filters.append(f"Current Company: {self.current_company}")
        if self.connections:
            filters.append(f"Connections: {self.connections}")
        return ", ".join(filters) if filters else "No filters"

class SearchFilters:
    def __init__(self, location=None, industry=None, current_company=None, connections=None, connection_of=None, followers_of=None):
        self.location = location
        self.industry = industry
        self.current_company = current_company
        self.connections = connections
        self.connection_of = connection_of
        self.followers_of = followers_of
        self.applied_params = {}
    
    def apply_with_scraper(self, scraper, query):
        url = scraper.search_and_apply_filters(
            query=query,
            location=self.location,
            industry=self.industry,
            current_company=self.current_company,
            connections=self.connections
        )
        
        self.applied_params = scraper.get_applied_filters()
        return url
    
    def is_empty(self):
        return not any([self.location, self.industry, self.current_company, self.connections, self.connection_of, self.followers_of])
    
    def __str__(self):
        filters = []
        if self.location:
            filters.append(f"Location: {self.location}")
        if self.industry:
            filters.append(f"Industry: {self.industry}")
        if self.current_company:
            filters.append(f"Current Company: {self.current_company}")
        if self.connections:
            filters.append(f"Connections: {self.connections}")
        if self.connection_of:
            filters.append(f"Connection of: {self.connection_of}")
        if self.followers_of:
            filters.append(f"Followers of: {self.followers_of}")
        return ", ".join(filters) if filters else "No filters"

def build_search_url(query, filters=None):
    base_url = "https://www.linkedin.com/search/results/people/"
    encoded_query = urllib.parse.quote(query)
    return f"{base_url}?keywords={encoded_query}"
