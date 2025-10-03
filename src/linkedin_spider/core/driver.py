import json
import logging
import os
import platform
import shutil
import subprocess
import zipfile
from pathlib import Path

import psutil
import requests
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_spider.core.config import ScraperConfig

logging.getLogger("seleniumwire").setLevel(logging.ERROR)
logging.getLogger("hpack").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


class DriverManager:
    """Manages Chrome WebDriver setup and lifecycle."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.driver: webdriver.Chrome | None = None
        self.wait: WebDriverWait | None = None
        self.actions: ActionChains | None = None
        self.profile_dir: Path | None = None
        self.cookies_file: Path | None = None

    def setup_driver(self) -> webdriver.Chrome:
        """Setup and configure Chrome WebDriver."""
        self._setup_profile_directory()
        self._terminate_existing_chrome_processes()

        chrome_options = self._create_chrome_options()
        seleniumwire_options = self._create_seleniumwire_options()

        driver_path = self._ensure_chromedriver()
        service = Service(executable_path=str(driver_path)) if driver_path else None

        try:
            if seleniumwire_options:
                self.driver = webdriver.Chrome(
                    service=service,
                    options=chrome_options,
                    seleniumwire_options=seleniumwire_options,
                )
            else:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            if "user data directory is already in use" in str(e).lower():
                self._terminate_existing_chrome_processes()
                if seleniumwire_options:
                    self.driver = webdriver.Chrome(
                        service=service,
                        options=chrome_options,
                        seleniumwire_options=seleniumwire_options,
                    )
                else:
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                raise Exception(f"Chrome driver initialization failed: {e}") from e

        self._configure_stealth_mode()
        self.wait = WebDriverWait(self.driver, self.config.page_load_timeout)
        self.actions = ActionChains(self.driver)

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
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument(
            f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}"
        )

        # Add compatibility and stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-extensions")

        for option in self.config.chrome_options:
            chrome_options.add_argument(option)

        chrome_options.add_argument(f"--user-agent={self.config.user_agent}")

        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_experimental_option("prefs", self.config.chrome_prefs)

        return chrome_options

    def _create_seleniumwire_options(self) -> dict:
        """Create selenium-wire options for proxy configuration."""
        if not self.config.proxy_server:
            return {}

        proxy_url = self.config.proxy_server
        return {
            "proxy": {
                "http": proxy_url,
                "https": proxy_url,
                "no_proxy": "localhost,127.0.0.1",
            }
        }

    def _configure_stealth_mode(self) -> None:
        """Configure stealth mode to avoid detection."""
        if not self.config.stealth_mode or not self.driver:
            return

        try:
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except Exception:
            pass

        if platform.system() == "Darwin":
            try:
                self.driver.execute_cdp_cmd(
                    "Emulation.setUserAgentOverride",
                    {
                        "userAgent": self.config.user_agent,
                        "acceptLanguage": "en-US,en;q=0.9",
                        "platform": "macOS",
                    },
                )

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
                    "Emulation.setTimezoneOverride", {"timezoneId": "America/New_York"}
                )
            except Exception:
                pass

        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument", {"source": self.config.stealth_script}
            )
        except Exception:
            pass

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

            # Detect architecture
            machine = platform.machine().lower()
            system = platform.system()

            if system == "Windows":
                platform_key = "win64" if "64" in machine or machine in ["amd64", "x86_64"] else "win32"
            elif system == "Darwin":
                platform_key = "mac-arm64" if machine == "arm64" else "mac-x64"
            elif system == "Linux":
                # Check for ARM64 architecture
                if machine in ["aarch64", "arm64"]:
                    # Chrome for Testing doesn't provide ARM64 Linux builds
                    # Need to use system chromedriver or build from source
                    logging.error(f"ARM64 Linux detected. ChromeDriver download not available for this architecture.")
                    logging.error(f"Please install chromium-chromedriver package: apt-get install chromium-chromedriver")
                    return None, None
                platform_key = "linux64"
            else:
                return None, None

            logging.info(f"Detected platform: {system}, architecture: {machine}, using: {platform_key}")

            for version_info in reversed(data["versions"]):
                if version_info["version"].startswith(major_version):
                    downloads = version_info.get("downloads", {}).get("chromedriver", [])

                    for download in downloads:
                        if download["platform"] == platform_key:
                            return download["url"], version_info["version"]

            fallback_urls = {
                "win64": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/win64/chromedriver-win64.zip",
                "win32": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/win32/chromedriver-win32.zip",
                "mac-x64": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/mac-x64/chromedriver-mac-x64.zip",
                "mac-arm64": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/mac-arm64/chromedriver-mac-arm64.zip",
                "linux64": f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.0.0/linux64/chromedriver-linux64.zip",
            }

            return fallback_urls.get(platform_key), f"{major_version}.0.0.0"

        except Exception:
            return None, None

    def _download_and_extract_chromedriver(self, download_url: str, version: str) -> Path | None:
        """Download and extract ChromeDriver."""
        try:
            drivers_dir = Path.home() / ".chromedriver"
            drivers_dir.mkdir(exist_ok=True)
            logging.info(f"Downloading ChromeDriver from: {download_url}")

            zip_path = drivers_dir / f"chromedriver_{version}.zip"

            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logging.info(f"Download complete. Extracting to: {drivers_dir}")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(drivers_dir)

            zip_path.unlink()

            executable_name = (
                "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
            )

            for file_path in drivers_dir.rglob(executable_name):
                if platform.system() != "Windows":
                    file_path.chmod(0o755)
                logging.info(f"ChromeDriver extracted to: {file_path}")
                return file_path

            logging.error(f"ChromeDriver executable '{executable_name}' not found after extraction")
            return None

        except Exception as e:
            logging.error(f"Failed to download/extract ChromeDriver: {e}")
            return None

    def _ensure_chromedriver(self) -> Path | None:
        """Ensure ChromeDriver is available."""
        chrome_version = self._get_chrome_version()
        if not chrome_version:
            chrome_version = "131.0.0.0"

        logging.info(f"Chrome version detected: {chrome_version}")

        # Check for version-matched driver in ~/.chromedriver first
        drivers_dir = Path.home() / ".chromedriver"
        if drivers_dir.exists():
            for file_path in drivers_dir.rglob("chromedriver*"):
                if file_path.is_file() and os.access(file_path, os.X_OK):
                    logging.info(f"Using cached ChromeDriver: {file_path}")
                    return file_path

        # Check CHROMEDRIVER_PATH env var
        env_path = os.environ.get("CHROMEDRIVER_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists() and os.access(path, os.X_OK):
                logging.info(f"Using ChromeDriver from CHROMEDRIVER_PATH: {path}")
                return path

        # Check system paths (especially important for ARM64 Linux)
        system_paths = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/snap/bin/chromium.chromedriver",  # Snap package
        ]

        for path_str in system_paths:
            path = Path(path_str)
            if path.exists() and os.access(path, os.X_OK):
                logging.info(f"Using system ChromeDriver: {path}")
                return path

        # Try to find via which command
        which_result = shutil.which("chromedriver")
        if which_result:
            logging.info(f"Using ChromeDriver from PATH: {which_result}")
            return Path(which_result)

        # Download version-matched driver (only for x86_64)
        machine = platform.machine().lower()
        if machine not in ["aarch64", "arm64"]:
            logging.info(f"Downloading ChromeDriver matching Chrome {chrome_version}...")
            download_url, version = self._get_chromedriver_download_url(chrome_version)
            if download_url:
                downloaded = self._download_and_extract_chromedriver(download_url, version)
                if downloaded:
                    logging.info(f"Successfully downloaded ChromeDriver to: {downloaded}")
                    return downloaded
                else:
                    logging.error("Failed to download ChromeDriver")

        # If we get here on ARM64, show helpful error
        if machine in ["aarch64", "arm64"]:
            logging.error("ChromeDriver not found on ARM64 Linux system")
            logging.error("Please install: apt-get install chromium-chromedriver")
            logging.error("Or for snap: snap install chromium")
        else:
            logging.error("Failed to get ChromeDriver download URL")

        return None
