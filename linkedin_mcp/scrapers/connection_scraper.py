import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ConnectionScraper:
    def __init__(self, driver, wait, human_behavior, tracking_handler):
        self.driver = driver
        self.wait = wait
        self.human_behavior = human_behavior
        self.tracking_handler = tracking_handler
    
    def scrape_incoming_connections(self, max_results=10):
        print(f"Scraping incoming connection requests (max: {max_results})")
        incoming_url = "https://www.linkedin.com/mynetwork/invitation-manager/received/"
        self.driver.get(incoming_url)
        self.human_behavior.human_delay(1, 3)
        self.human_behavior.simulate_reading_behavior(1, 2)
        
        connections = []
        
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='listitem'][componentkey]")
            ))
            
            while len(connections) < max_results:
                containers = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'][componentkey]")
                processed_containers = self.tracking_handler.handle_search_result_tracking(containers)
                
                for container in processed_containers:
                    if len(connections) >= max_results:
                        break
                        
                    data = self._extract_incoming_connection_data(container)
                    if data and data not in connections:
                        connections.append(data)
                
                if not self._handle_load_more() or len(connections) >= max_results:
                    break
            
            print(f"[SUCCESS] Extracted {len(connections)} incoming connections")
            return connections
            
        except Exception as e:
            print(f"[ERROR] Error scraping incoming connections: {str(e)}")
            return []
    
    def scrape_outgoing_connections(self, max_results=10):
        print(f"Scraping outgoing connection requests (max: {max_results})")
        outgoing_url = "https://www.linkedin.com/mynetwork/invitation-manager/sent/"
        self.driver.get(outgoing_url)
        self.human_behavior.human_delay(1, 3)
        self.human_behavior.simulate_reading_behavior(1, 2)
        
        connections = []
        
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='listitem'][componentkey]")
            ))
            
            while len(connections) < max_results:
                containers = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'][componentkey]")
                processed_containers = self.tracking_handler.handle_search_result_tracking(containers)
                
                for container in processed_containers:
                    if len(connections) >= max_results:
                        break
                        
                    data = self._extract_outgoing_connection_data(container)
                    if data and data not in connections:
                        connections.append(data)
                
                if not self._handle_load_more() or len(connections) >= max_results:
                    break
            
            print(f"[SUCCESS] Extracted {len(connections)} outgoing connections")
            return connections
            
        except Exception as e:
            print(f"[ERROR] Error scraping outgoing connections: {str(e)}")
            return []
    
    def scrape_connections(self, connection_type="both", max_results=10):
        results = {}
        
        if connection_type in ["both", "incoming"]:
            results["incoming"] = self.scrape_incoming_connections(max_results)
        
        if connection_type in ["both", "outgoing"]:
            results["outgoing"] = self.scrape_outgoing_connections(max_results)
        
        return results
    
    def _extract_incoming_connection_data(self, container):
        data = {}
        
        try:
            name_el = container.find_element(By.CSS_SELECTOR, "a[href*='/in/'] strong")
            data["name"] = name_el.text.strip()
        except:
            try:
                name_el = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
                data["name"] = name_el.text.strip()
            except:
                data["name"] = "N/A"
        
        try:
            profile_link = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            data["profile_url"] = profile_link.get_attribute("href")
        except:
            data["profile_url"] = "N/A"
        
        try:
            headline_els = container.find_elements(By.CSS_SELECTOR, "p")
            for p in headline_els:
                text = p.text.strip()
                if text and "@" in text or any(word in text.lower() for word in ["engineer", "developer", "manager", "director", "founder", "ceo", "cto"]):
                    data["headline"] = text
                    break
            if "headline" not in data:
                data["headline"] = headline_els[1].text.strip() if len(headline_els) > 1 else "N/A"
        except:
            data["headline"] = "N/A"
        
        try:
            mutual_el = container.find_element(By.CSS_SELECTOR, "p:contains('mutual connection')")
            data["mutual_connections"] = mutual_el.text.strip()
        except:
            try:
                mutual_els = container.find_elements(By.CSS_SELECTOR, "p")
                for p in mutual_els:
                    text = p.text.strip()
                    if "mutual connection" in text.lower():
                        data["mutual_connections"] = text
                        break
                if "mutual_connections" not in data:
                    data["mutual_connections"] = "N/A"
            except:
                data["mutual_connections"] = "N/A"
        
        try:
            time_els = container.find_elements(By.CSS_SELECTOR, "p")
            for p in time_els:
                text = p.text.strip()
                if any(word in text.lower() for word in ["ago", "month", "week", "day", "hour"]):
                    data["time_sent"] = text
                    break
            if "time_sent" not in data:
                data["time_sent"] = "N/A"
        except:
            data["time_sent"] = "N/A"
        
        try:
            span_element = container.find_element(By.CSS_SELECTOR, "span[data-testid='expandable-text-box']")
            message_text = self.driver.execute_script("""
                var element = arguments[0];
                var text = '';
                for (var i = 0; i < element.childNodes.length; i++) {
                    if (element.childNodes[i].nodeType === Node.TEXT_NODE) {
                        text += element.childNodes[i].textContent;
                    }
                }
                return text.trim();
            """, span_element)

            data["message"] = message_text
        except:
            data["message"] = "N/A"
        
        try:
            img_el = container.find_element(By.CSS_SELECTOR, "img[alt*='profile picture']")
            data["image_url"] = img_el.get_attribute("src")
        except:
            data["image_url"] = "N/A"
        
        return data if data.get("name") != "N/A" else None
    
    def _extract_outgoing_connection_data(self, container):
        data = {}
        
        try:
            name_el = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            data["name"] = name_el.text.strip()
        except:
            data["name"] = "N/A"
        
        try:
            profile_link = container.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            data["profile_url"] = profile_link.get_attribute("href")
        except:
            data["profile_url"] = "N/A"
        
        try:
            headline_els = container.find_elements(By.CSS_SELECTOR, "p")
            for p in headline_els:
                text = p.text.strip()
                if text and "@" in text or any(word in text.lower() for word in ["engineer", "developer", "manager", "director", "founder", "ceo", "cto"]):
                    data["headline"] = text
                    break
            if "headline" not in data:
                data["headline"] = headline_els[1].text.strip() if len(headline_els) > 1 else "N/A"
        except:
            data["headline"] = "N/A"
        
        try:
            time_els = container.find_elements(By.CSS_SELECTOR, "p")
            for p in time_els:
                text = p.text.strip()
                if "sent" in text.lower() and any(word in text.lower() for word in ["ago", "month", "week", "day", "hour"]):
                    data["time_sent"] = text
                    break
            if "time_sent" not in data:
                data["time_sent"] = "N/A"
        except:
            data["time_sent"] = "N/A"
        
        try:
            span_element = container.find_element(By.CSS_SELECTOR, "span[data-testid='expandable-text-box']")
            message_text = self.driver.execute_script("""
                var element = arguments[0];
                var text = '';
                for (var i = 0; i < element.childNodes.length; i++) {
                    if (element.childNodes[i].nodeType === Node.TEXT_NODE) {
                        text += element.childNodes[i].textContent;
                    }
                }
                return text.trim();
            """, span_element)

            data["message"] = message_text
        except:
            data["message"] = "N/A"
        
        try:
            img_el = container.find_element(By.CSS_SELECTOR, "img[alt*='profile picture']")
            data["image_url"] = img_el.get_attribute("src")
        except:
            data["image_url"] = "N/A"
        
        return data if data.get("name") != "N/A" else None
    
    def _handle_load_more(self):
        try:
            load_more_btn = self.driver.find_element(By.CSS_SELECTOR, "button:contains('Load more')")
            if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                self.human_behavior.human_delay(0.5, 1.5)
                load_more_btn.click()
                self.human_behavior.human_delay(2, 4)
                return True
        except:
            try:
                load_more_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Load more')]")
                if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                    self.human_behavior.human_delay(0.5, 1.5)
                    load_more_btn.click()
                    self.human_behavior.human_delay(2, 4)
                    return True
            except:
                pass
        return False
