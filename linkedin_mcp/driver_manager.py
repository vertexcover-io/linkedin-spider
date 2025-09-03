from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import random
from config import ScraperConfig

class DriverManager:
    def __init__(self, headless=False, stealth_mode=True):
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.driver = None
        self.wait = None
        self.actions = None
        
    def setup_driver(self):
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            
        for option in ScraperConfig.CHROME_OPTIONS:
            chrome_options.add_argument(option)
            
        chrome_options.add_argument(f"--user-agent={ScraperConfig.get_random_user_agent()}")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("prefs", ScraperConfig.CHROME_PREFS)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        if self.stealth_mode:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": ScraperConfig.STEALTH_SCRIPT
            })
            
        self.wait = WebDriverWait(self.driver, 15)
        self.actions = ActionChains(self.driver)
        
        return self.driver
        
    def close(self):
        if self.driver:
            self.driver.quit()