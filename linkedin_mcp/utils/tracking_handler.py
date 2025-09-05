import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .csp_bypass import CSPBypassHandler

class LinkedInTrackingHandler:
    def __init__(self, driver, wait, actions):
        self.driver = driver
        self.wait = wait
        self.actions = actions
        self.csp_bypass = CSPBypassHandler(driver)
        
    def wait_for_element_impression(self, element, min_duration=0.3):
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            short_wait = WebDriverWait(self.driver, 2)
            short_wait.until(EC.visibility_of(element))
            
            if self.csp_bypass.simulate_natural_interaction(element):
                time.sleep(max(min_duration, 0.1))
                return True
                
            return False
            
        except Exception:
            return False
            
    def simulate_interaction_types(self):
        try:
            if random.random() < 0.7:
                scroll_distance = random.randint(100, 400)
                try:
                    can_scroll = self.driver.execute_script("""
                        return (window.pageYOffset || document.documentElement.scrollTop) < 
                               (document.documentElement.scrollHeight - document.documentElement.clientHeight);
                    """)
                    if can_scroll:
                        self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                except Exception:
                    pass
                
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, .clickable")
                if elements:
                    random_element = random.choice(elements[:10])
                    self.actions.move_to_element(random_element).perform()
                    time.sleep(random.uniform(0.1, 0.3))
                    
            except Exception:
                pass
                
        except Exception:
            pass
            
    def handle_search_result_tracking(self, containers):
        processed_containers = []
        
        for container in containers:
            try:
                self.wait_for_element_impression(container, 0.2)
                
                try:
                    if container.get_attribute('data-view-name') == 'search-entity-result-universal-template':
                        container.click()
                        time.sleep(0.05)
                        self.driver.execute_script("window.history.back();")
                        time.sleep(0.05)
                except:
                    pass
                
                processed_containers.append(container)
                
            except Exception:
                continue
                
        return processed_containers
        
    def inject_enhanced_tracking_fixes(self):
        try:
            self.csp_bypass.handle_csp_violation()
            self.csp_bypass.suppress_tracking_errors()
            
            self.driver.execute_cdp_cmd('Page.setBypassCSP', {'enabled': True})
            
            time.sleep(0.3)
            
        except Exception:
            pass