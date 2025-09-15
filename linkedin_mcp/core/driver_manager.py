from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import random
import os
import platform
import requests
import zipfile
import shutil
import subprocess
import json
import tempfile
from .config import ScraperConfig

class DriverManager:
    def __init__(self, headless=True, stealth_mode=True):
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.driver = None
        self.wait = None
        self.actions = None
        self.profile_dir = None
        self.cookies_file = None
        
    def _get_chrome_version(self):
        try:
            if platform.system() == "Windows":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version
            elif platform.system() == "Darwin":
                result = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], 
                                      capture_output=True, text=True)
                return result.stdout.strip().split()[-1]
            else:
                result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
                return result.stdout.strip().split()[-1]
        except Exception:
            return None
    
    def _get_chromedriver_download_url(self, version):
        major_version = version.split('.')[0]
        
        try:
            api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            for version_info in reversed(data['versions']):
                if version_info['version'].startswith(major_version):
                    downloads = version_info.get('downloads', {}).get('chromedriver', [])
                    
                    system_map = {
                        'Windows': 'win64',
                        'Darwin': 'mac-x64', 
                        'Linux': 'linux64'
                    }
                    
                    platform_key = system_map.get(platform.system())
                    if platform_key:
                        for download in downloads:
                            if download['platform'] == platform_key:
                                return download['url'], version_info['version']
            
            fallback_urls = {
                'Windows': f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/win64/chromedriver-win64.zip",
                'Darwin': f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/mac-x64/chromedriver-mac-x64.zip",
                'Linux': f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/linux64/chromedriver-linux64.zip"
            }
            
            return fallback_urls.get(platform.system()), f"{major_version}.0.0.0"
            
        except Exception:
            return None, None
    
    def _download_and_extract_chromedriver(self, download_url, version):
        try:
            drivers_dir = os.path.join(os.path.expanduser("~"), ".chromedriver")
            os.makedirs(drivers_dir, exist_ok=True)
            
            zip_path = os.path.join(drivers_dir, f"chromedriver_{version}.zip")
            
            print(f"Downloading ChromeDriver {version}...")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Extracting ChromeDriver...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(drivers_dir)
            
            os.remove(zip_path)
            
            system = platform.system()
            if system == "Windows":
                executable_name = "chromedriver.exe"
            else:
                executable_name = "chromedriver"
            
            for root, dirs, files in os.walk(drivers_dir):
                if executable_name in files:
                    driver_path = os.path.join(root, executable_name)
                    if system != "Windows":
                        os.chmod(driver_path, 0o755)
                    print(f"ChromeDriver installed at: {driver_path}")
                    return driver_path
            
            return None
            
        except Exception as e:
            print(f"Error downloading ChromeDriver: {e}")
            return None
    
    def _find_existing_chromedriver(self):
        env_path = os.environ.get('CHROMEDRIVER_PATH')
        if env_path and os.path.exists(env_path) and os.access(env_path, os.X_OK):
            return env_path
            
        possible_locations = []
        
        drivers_dir = os.path.join(os.path.expanduser("~"), ".chromedriver")
        if os.path.exists(drivers_dir):
            for root, dirs, files in os.walk(drivers_dir):
                for file in files:
                    if file.startswith("chromedriver"):
                        possible_locations.append(os.path.join(root, file))
        
        system_paths = {
            'Windows': ['chromedriver.exe', 'chromedriver'],
            'Darwin': ['/usr/local/bin/chromedriver', '/usr/bin/chromedriver'],
            'Linux': ['/usr/local/bin/chromedriver', '/usr/bin/chromedriver']
        }
        
        for path in system_paths.get(platform.system(), []):
            if shutil.which(path) or os.path.exists(path):
                possible_locations.append(path)
        
        for path in possible_locations:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def _ensure_chromedriver(self):
        existing_driver = self._find_existing_chromedriver()
        if existing_driver:
            return existing_driver
        
        print("ChromeDriver not found. Installing...")
        
        chrome_version = self._get_chrome_version()
        if not chrome_version:
            print("Could not detect Chrome version. Using latest ChromeDriver.")
            chrome_version = "131.0.0.0"
        
        download_url, version = self._get_chromedriver_download_url(chrome_version)
        if not download_url:
            print("Could not find compatible ChromeDriver download URL.")
            return None
        
        return self._download_and_extract_chromedriver(download_url, version)

    def _setup_profile_directory(self):
        profile_base = os.path.join(os.getcwd(), ".linkedin_scraper_profiles")
        os.makedirs(profile_base, exist_ok=True)

        self.profile_dir = os.path.join(profile_base, "default_profile")
        os.makedirs(self.profile_dir, exist_ok=True)

        self.cookies_file = os.path.join(self.profile_dir, "cookies.json")
        return self.profile_dir

    def save_cookies(self):
        if not self.driver or not self.cookies_file:
            return False

        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            return True
        except Exception as e:
            print(f"Error saving cookies: {e}")
            return False

    def load_cookies(self):
        if not self.driver or not self.cookies_file or not os.path.exists(self.cookies_file):
            return False

        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    continue
            return True
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return False

    def clear_saved_cookies(self):
        if self.cookies_file and os.path.exists(self.cookies_file):
            try:
                os.remove(self.cookies_file)
                return True
            except Exception:
                return False
        return True

    def setup_driver(self):
        chrome_options = Options()

        profile_dir = self._setup_profile_directory()
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        chrome_path = os.environ.get('CHROME_PATH')
        if chrome_path and os.path.exists(chrome_path):
            chrome_options.binary_location = chrome_path

        if self.headless:
            chrome_options.add_argument("--headless")

        for option in ScraperConfig.get_chrome_options_for_platform():
            chrome_options.add_argument(option)

        chrome_options.add_argument(f"--user-agent={ScraperConfig.get_random_user_agent()}")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("prefs", ScraperConfig.CHROME_PREFS)

        chrome_options.add_argument("--keep-alive-for-test")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--remote-allow-origins=*")
        
        try:
            driver_path = self._ensure_chromedriver()
            if driver_path:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                print("Attempting to use system ChromeDriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Chrome with custom driver: {e}")
            try:
                print("Falling back to system ChromeDriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as fallback_error:
                print("\nChrome setup failed. Please ensure:")
                print("1. Google Chrome is installed")
                print("2. Chrome version is compatible")
                print("3. Internet connection is available")
                raise Exception(f"Chrome driver initialization failed: {fallback_error}")
        
        if self.stealth_mode:
            try:
                self.driver.execute_script("try { if (!Object.getOwnPropertyDescriptor(navigator, 'webdriver')) { Object.defineProperty(navigator, 'webdriver', {get: () => undefined, configurable: true}); } } catch(e) {}")
            except Exception:
                pass

            if platform.system() == "Darwin":
                try:
                    self.driver.execute_cdp_cmd('Emulation.setUserAgentOverride', {
                        'userAgent': ScraperConfig.get_random_user_agent(),
                        'acceptLanguage': 'en-US,en;q=0.9',
                        'platform': 'macOS'
                    })

                    self.driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                        'width': 1920,
                        'height': 1080,
                        'deviceScaleFactor': 2,
                        'mobile': False
                    })

                    self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                        'timezoneId': 'America/New_York'
                    })
                except Exception:
                    pass

            try:
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    "source": ScraperConfig.STEALTH_SCRIPT
                })
            except Exception:
                pass
            
        self.wait = WebDriverWait(self.driver, 15)
        self.actions = ActionChains(self.driver)
        
        return self.driver
        
    def close(self):
        if self.driver:
            self.driver.quit()