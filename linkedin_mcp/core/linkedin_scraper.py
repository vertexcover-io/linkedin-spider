import json
import time
import random
from .driver_manager import DriverManager
from .authentication import LinkedInAuth
from ..utils.human_behavior import HumanBehavior
from ..utils.tracking_handler import LinkedInTrackingHandler
from ..scrapers.profile_scraper import ProfileScraper
from ..scrapers.search_scraper import SearchScraper

class LinkedInScraper:
    def __init__(self, email=None, password=None, li_at_cookie=None, headless=False,
                 stealth_mode=True):
        self.email = email
        self.password = password
        self.li_at_cookie = li_at_cookie
        
        self.driver_manager = DriverManager(headless, stealth_mode)
        self.driver = self.driver_manager.setup_driver()
        self.wait = self.driver_manager.wait
        self.actions = self.driver_manager.actions
        
        self.human_behavior = HumanBehavior(self.driver, self.wait, self.actions)
        self.tracking_handler = LinkedInTrackingHandler(self.driver, self.wait, self.actions)
        self.auth = LinkedInAuth(self.driver, self.wait, self.human_behavior, 
                                email, password, li_at_cookie)
        
        self.profile_scraper = ProfileScraper(self.driver, self.wait, self.human_behavior, self.tracking_handler)
        self.search_scraper = SearchScraper(self.driver, self.wait, self.human_behavior, self.tracking_handler)
        
        self._initialize_tracking_fixes()
        self.auth.authenticate()
        
    def _initialize_tracking_fixes(self):
        self.tracking_handler.inject_enhanced_tracking_fixes()
        
    def scrape_profile(self, profile_url):
        return self.profile_scraper.scrape_profile(profile_url)
        
    def search_profiles(self, query, max_results=10, filters=None):
        return self.search_scraper.search_profiles(query, max_results, filters)
        
    def extract_headless_data(self):
        return self.search_scraper.extract_headless_data()
        
    def scrape_search_results(self, query, max_results=5, filters=None):
        profile_urls = self.search_profiles(query, max_results, filters)
        
        if not profile_urls:
            print("No profile URLs found, but checking for anonymous data...")
            anonymous_data = self.extract_headless_data()
            if anonymous_data:
                print(f"[SUCCESS] Extracted {len(anonymous_data)} anonymous profiles from search results")
                return anonymous_data
            else:
                print("[ERROR] No data could be extracted from search results")
                return []
                
        profiles_data = []
        
        for i, profile_info in enumerate(profile_urls, 1):
            print(f"\nScraping profile {i}/{len(profile_urls)}")
            
            if i > 1:
                delay = random.uniform(2, 5)
                print(f"[WAIT] Waiting {delay:.1f} seconds before next profile (human behavior)...")
                time.sleep(delay)
                
            profile_url = profile_info.get('profile_url')
            if profile_url and profile_url != "N/A" and isinstance(profile_url, str) and 'linkedin.com/in/' in profile_url:
                profile_data = self.scrape_profile(profile_url)
                
                if profile_data:
                    profiles_data.append(profile_data)
            else:
                print(f"[WARNING] Skipping profile with invalid URL: {profile_info.get('name', 'Unknown')}")
                if profile_info.get('name') != 'N/A' or profile_info.get('headline') != 'N/A':
                    limited_data = {
                        'name': profile_info.get('name', 'N/A'),
                        'headline': profile_info.get('headline', 'N/A'),
                        'location': profile_info.get('location', 'N/A'),
                        'profile_url': 'N/A',
                        'about': 'N/A',
                        'experience': []
                    }
                    profiles_data.append(limited_data)
                
            if random.random() < 0.2 and i < len(profile_urls):
                print("[INFO] Simulating tab management behavior...")
                self.driver.execute_script("window.blur();")
                self.human_behavior.human_delay(1, 3)
                self.driver.execute_script("window.focus();")
                
        return profiles_data
        
    def save_to_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Data saved to {filename}")
        
    def close(self):
        if self.driver_manager:
            self.human_behavior.human_delay(1, 2)
            self.driver_manager.close()
            print("Browser closed.")
    
    def keep_alive(self):
        try:
            self.driver.execute_script("return window.location.href;")
            return True
        except:
            return False