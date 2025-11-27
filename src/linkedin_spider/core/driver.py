import contextlib
import json
import logging
import os
import platform
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Dict, Optional

import psutil
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.core.config import ScraperConfig, get_default_user_agent

# Global driver storage to reuse sessions
active_drivers: Dict[str, webdriver.Chrome] = {}

logger = logging.getLogger(__name__)


class DriverManager:
    """Manages Chrome WebDriver setup and lifecycle."""

    def __init__(self, config: ScraperConfig, session_id: str = "default"):
        self.config = config
        self.session_id = session_id
        self.driver: webdriver.Chrome | None = None
        self.wait: WebDriverWait | None = None
        self.actions: ActionChains | None = None
        self.profile_dir: Path | None = None
        self.cookies_file: Path | None = None

    def setup_driver(self, reuse_session: bool = True) -> webdriver.Chrome:
        """Setup and configure Chrome WebDriver with optional session reuse.

        Args:
            reuse_session: If True, reuse existing driver if available

        Returns:
            Configured Chrome WebDriver instance
        """
        # Always setup profile directory for cookies file path
        self._setup_profile_directory()

        # Check for existing driver in global storage
        if reuse_session and self.session_id in active_drivers:
            logger.info("Using existing Chrome WebDriver session")
            self.driver = active_drivers[self.session_id]
            self.wait = WebDriverWait(self.driver, self.config.page_load_timeout)
            self.actions = ActionChains(self.driver)
            return self.driver

        self._terminate_existing_chrome_processes()

        chrome_options = self._create_chrome_options()
        print("chrome_options",chrome_options)

        try:
            driver_path = self._ensure_chromedriver()
            if driver_path:
                service = Service(str(driver_path))
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            # If we still get the user-data-dir error, try terminating processes again
            if "user data directory is already in use" in str(e).lower():
                self._terminate_existing_chrome_processes()
                try:
                    if driver_path:
                        service = Service(str(driver_path))
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    else:
                        self.driver = webdriver.Chrome(options=chrome_options)
                except Exception:
                    try:
                        self.driver = webdriver.Chrome(options=chrome_options)
                    except Exception as fallback_error:
                        raise Exception(
                            f"Chrome driver initialization failed: {fallback_error}"
                        ) from e
            else:
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                except Exception as fallback_error:
                    raise Exception(f"Chrome driver initialization failed: {fallback_error}") from e

        self._configure_stealth_mode()
        self.wait = WebDriverWait(self.driver, self.config.page_load_timeout)
        self.actions = ActionChains(self.driver)

        # Store in global active_drivers for reuse
        if reuse_session:
            active_drivers[self.session_id] = self.driver
            logger.info("Chrome WebDriver session created and stored for reuse")

        return self.driver

    def save_cookies(self) -> bool:
        """Save current session cookies."""
        if not self.driver or not self.cookies_file:
            return False

        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, "w") as f:
                json.dump(cookies, f)
            return True
        except Exception:
            return False

    def load_cookies(self) -> bool:
        """Load saved cookies into current session."""
        print("self.cookies_file",self.cookies_file)
        if not self.driver or not self.cookies_file or not self.cookies_file.exists():
            return False

        try:
            with open(self.cookies_file) as f:
                cookies = json.load(f)

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    continue
            return True
        except Exception:
            return False

    def clear_saved_cookies(self) -> bool:
        """Clear saved cookies file."""
        if self.cookies_file and self.cookies_file.exists():
            try:
                self.cookies_file.unlink()
                return True
            except Exception:
                return False
        return True

    def close(self) -> None:
        """Close the WebDriver session."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _terminate_existing_chrome_processes(self) -> None:
        """Terminate existing Chrome processes that might be using the same user data directory."""
        if not self.profile_dir:
            return

        try:
            profile_path_str = str(self.profile_dir.resolve())
            terminated_count = 0
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["name"] and "chrome" in proc.info["name"].lower():
                        cmdline = proc.info["cmdline"]
                        if cmdline and isinstance(cmdline, list):
                            cmdline_str = " ".join(cmdline)
                            if (
                                f"--user-data-dir={profile_path_str}" in cmdline_str
                                or f'--user-data-dir="{profile_path_str}"' in cmdline_str
                            ):
                                try:
                                    process = psutil.Process(proc.info["pid"])
                                    process.terminate()
                                    terminated_count += 1
                                    try:
                                        process.wait(timeout=3)
                                    except psutil.TimeoutExpired:
                                        process.kill()
                                except (
                                    psutil.NoSuchProcess,
                                    psutil.AccessDenied,
                                    psutil.ZombieProcess,
                                ):
                                    pass
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            if terminated_count > 0:
                print(
                    f"Terminated {terminated_count} Chrome processes using profile: {profile_path_str}"
                )
                # Give some time for the processes to fully terminate and release file locks
                import time

                time.sleep(1)

        except Exception as e:
            # Don't fail the entire setup if we can't terminate processes
            print(f"Warning: Could not terminate existing Chrome processes: {e}")
            pass

    def _setup_profile_directory(self) -> None:
        """Setup profile directory for persistent sessions."""
        profile_base = Path.home() / ".linkedin_spider_profiles"
        profile_base.mkdir(exist_ok=True)

        self.profile_dir = profile_base / "default_profile"
        self.profile_dir.mkdir(exist_ok=True)

        self.cookies_file = self.profile_dir / "cookies.json"

    def _create_chrome_options(self) -> Options:
        """Create Chrome options with all necessary configurations."""
        chrome_options = Options()

        if self.profile_dir:
            chrome_options.add_argument(f"--user-data-dir={self.profile_dir}")
            chrome_options.add_argument("--profile-directory=Default")

        chrome_path = os.environ.get("CHROME_PATH")
        if chrome_path and Path(chrome_path).exists():
            chrome_options.binary_location = chrome_path

        if self.config.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument(
            f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}"
        )

        for option in self.config.chrome_options:
            chrome_options.add_argument(option)
        print("self.config.user_agent",self.config.user_agent)

        chrome_options.add_argument(f"--user-agent={self.config.user_agent}")

        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("prefs", self.config.chrome_prefs)

        return chrome_options

    def _configure_stealth_mode(self) -> None:
        """Configure stealth mode to avoid detection."""
        if not self.driver:
            return

        with contextlib.suppress(Exception):
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        # Set user agent via CDP for all platforms (works reliably in both headless and non-headless)
        try:
            platform_name = {
                "Windows": "Win32",
                "Darwin": "MacIntel",
                "Linux": "Linux x86_64"
            }.get(platform.system(), "Win32")

            self.driver.execute_cdp_cmd(
                "Emulation.setUserAgentOverride",
                {
                    "userAgent": self.config.user_agent,
                    "acceptLanguage": "en-US,en;q=0.9",
                    "platform": platform_name,
                },
            )
        except Exception:
            pass

        if self.config.stealth_mode:
            if platform.system() == "Darwin":
                try:
                    self.driver.execute_cdp_cmd(
                        "Emulation.setDeviceMetricsOverride",
                        {
                            "width": self.config.window_size[0],
                            "height": self.config.window_size[1],
                            "deviceScaleFactor": 2,
                            "mobile": False,
                        },
                    )

                    self.driver.execute_cdp_cmd(
                        "Emulation.setTimezoneOverride", {"timezoneId": "India/Kolkata"}
                    )
                except Exception:
                    pass

            with contextlib.suppress(Exception):
                self.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument", {"source": self.config.stealth_script}
                )

    def _get_chrome_version(self) -> str | None:
        """Get installed Chrome version."""
        try:
            if platform.system() == "Windows":
                import winreg

                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip().split()[-1]
            else:
                result = subprocess.run(
                    ["google-chrome", "--version"], capture_output=True, text=True
                )
                return result.stdout.strip().split()[-1]
        except Exception:
            return None

    def _get_chromedriver_download_url(self, version: str) -> tuple[str | None, str | None]:
        """Get ChromeDriver download URL for given Chrome version."""
        major_version = version.split(".")[0]

        try:
            api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            response = requests.get(api_url, timeout=10)
            data = response.json()

            system_map = {"Windows": "win64", "Darwin": "mac-x64", "Linux": "linux64"}

            platform_key = system_map.get(platform.system())
            if not platform_key:
                return None, None

            for version_info in reversed(data["versions"]):
                if version_info["version"].startswith(major_version):
                    downloads = version_info.get("downloads", {}).get("chromedriver", [])

                    for download in downloads:
                        if download["platform"] == platform_key:
                            return download["url"], version_info["version"]

            fallback_urls = {
                "Windows": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/win64/chromedriver-win64.zip",
                "Darwin": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/mac-x64/chromedriver-mac-x64.zip",
                "Linux": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/linux64/chromedriver-linux64.zip",
            }

            return fallback_urls.get(platform.system()), f"{major_version}.0.0.0"

        except Exception:
            return None, None

    def _download_and_extract_chromedriver(self, download_url: str, version: str) -> Path | None:
        """Download and extract ChromeDriver."""
        try:
            drivers_dir = Path.home() / ".chromedriver"
            drivers_dir.mkdir(exist_ok=True)

            zip_path = drivers_dir / f"chromedriver_{version}.zip"

            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(drivers_dir)

            zip_path.unlink()

            executable_name = (
                "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
            )

            for file_path in drivers_dir.rglob(executable_name):
                if platform.system() != "Windows":
                    file_path.chmod(0o755)
                return file_path

            return None

        except Exception:
            return None

    def _find_existing_chromedriver(self) -> Path | None:
        """Find existing ChromeDriver installation."""
        env_path = os.environ.get("CHROMEDRIVER_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists() and os.access(path, os.X_OK):
                return path

        drivers_dir = Path.home() / ".chromedriver"
        if drivers_dir.exists():
            for file_path in drivers_dir.rglob("chromedriver*"):
                if file_path.is_file() and os.access(file_path, os.X_OK):
                    return file_path

        system_paths = {
            "Windows": ["chromedriver.exe", "chromedriver"],
            "Darwin": ["/usr/local/bin/chromedriver", "/usr/bin/chromedriver"],
            "Linux": ["/usr/local/bin/chromedriver", "/usr/bin/chromedriver"],
        }

        for path_str in system_paths.get(platform.system(), []):
            if shutil.which(path_str):
                return Path(path_str)
            path = Path(path_str)
            if path.exists() and os.access(path, os.X_OK):
                return path

        return None

    def _ensure_chromedriver(self) -> Path | None:
        """Ensure ChromeDriver is available."""
        existing_driver = self._find_existing_chromedriver()
        if existing_driver:
            return existing_driver

        chrome_version = self._get_chrome_version()
        if not chrome_version:
            chrome_version = "131.0.0.0"

        download_url, version = self._get_chromedriver_download_url(chrome_version)
        if not download_url:
            return None

        return self._download_and_extract_chromedriver(download_url, version)

    def login_with_cookie(self, cookie: str) -> bool:
        """
        Log in to LinkedIn using session cookie with improved validation.

        Args:
            cookie: LinkedIn session cookie (li_at value)

        Returns:
            bool: True if login was successful, False otherwise
        """
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        try:
            logger.info("Attempting cookie authentication...")

            # Set longer timeout to handle slow LinkedIn loading
            # Invalid cookies cause indefinite loading, so timeout is our detection mechanism
            original_timeout = self.driver.timeouts.page_load
            self.driver.set_page_load_timeout(45)

            # Navigate to LinkedIn first
            try:
                self.driver.get("https://www.linkedin.com")
                time.sleep(1)
            except TimeoutException:
                logger.warning("Initial page load timeout")
                self.driver.set_page_load_timeout(original_timeout)
                return False

            # Add the cookie
            cookie_value = cookie.replace("li_at=", "").strip()
            self.driver.add_cookie({
                "name": "li_at",
                "value": cookie_value,
                "domain": ".linkedin.com",
                "path": "/",
                "secure": True,
            })

            # Refresh to apply cookie
            try:
                self.driver.refresh()
                time.sleep(2)
            except TimeoutException:
                logger.warning("Cookie authentication failed - page load timeout (likely invalid cookie)")
                self.driver.set_page_load_timeout(original_timeout)
                return False

            # Check authentication status by examining the current URL
            try:
                current_url = self.driver.current_url

                # Check if we're on login page (authentication failed)
                if "login" in current_url or "uas/login" in current_url:
                    logger.warning("Cookie authentication failed - redirected to login page")
                    self.driver.set_page_load_timeout(original_timeout)
                    return False

                # Check if we're on authenticated pages (authentication succeeded)
                elif any(indicator in current_url for indicator in ["feed", "mynetwork", "linkedin.com/in/", "/feed/"]):
                    logger.info("Cookie authentication successful")
                    self.driver.set_page_load_timeout(original_timeout)
                    return True

                # Unexpected page - wait briefly and check again
                else:
                    logger.info("Unexpected page after login, checking authentication status...")
                    time.sleep(2)

                    final_url = self.driver.current_url
                    if "login" in final_url or "uas/login" in final_url:
                        logger.warning("Cookie authentication failed - ended on login page")
                        self.driver.set_page_load_timeout(original_timeout)
                        return False
                    elif any(indicator in final_url for indicator in ["feed", "mynetwork", "linkedin.com/in/", "/feed/"]):
                        logger.info("Cookie authentication successful after verification")
                        self.driver.set_page_load_timeout(original_timeout)
                        return True
                    else:
                        logger.warning(f"Cookie authentication uncertain - unexpected final page: {final_url}")
                        self.driver.set_page_load_timeout(original_timeout)
                        return False

            except Exception as e:
                logger.error(f"Error checking authentication status: {e}")
                self.driver.set_page_load_timeout(original_timeout)
                return False

        except Exception as e:
            logger.error(f"Cookie authentication failed with error: {e}")
            if self.driver:
                try:
                    self.driver.set_page_load_timeout(original_timeout or 30)
                except Exception:
                    pass
            return False

    def get_active_driver(self) -> Optional[webdriver.Chrome]:
        """
        Get the currently active driver without creating a new one.

        Returns:
            Optional[webdriver.Chrome]: Active driver if available, None otherwise
        """
        return active_drivers.get(self.session_id)

    def capture_session_cookie(self) -> Optional[str]:
        """
        Capture LinkedIn session cookie from driver.

        Returns:
            Optional[str]: Session cookie if found, None otherwise
        """
        if not self.driver:
            return None

        try:
            # Get li_at cookie which is the main LinkedIn session cookie
            cookie = self.driver.get_cookie("li_at")
            if cookie and cookie.get("value"):
                return f"li_at={cookie['value']}"
            return None
        except Exception as e:
            logger.warning(f"Failed to capture session cookie: {e}")
            return None

    @staticmethod
    def close_all_drivers() -> None:
        """Close all active drivers and clean up resources."""
        global active_drivers

        for session_id, driver in active_drivers.items():
            try:
                logger.info(f"Closing Chrome WebDriver session: {session_id}")
                driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver {session_id}: {e}")

        active_drivers.clear()
        logger.info("All Chrome WebDriver sessions closed")
