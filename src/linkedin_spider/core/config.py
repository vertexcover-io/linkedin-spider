import platform
from dataclasses import dataclass


def get_default_user_agent() -> str:
    """Get platform-specific default user agent to reduce fingerprinting."""
    system = platform.system()

    if system == "Windows":
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    elif system == "Darwin":  # macOS
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    else:  # Linux and others
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"


@dataclass
class ScraperConfig:
    """Configuration settings for LinkedIn scraper."""

    headless: bool = False
    stealth_mode: bool = True
    window_size: tuple[int, int] = (1920, 1080)
    page_load_timeout: int = 30
    implicit_wait: int = 10

    human_delay_range: tuple[float, float] = (0.5, 2.0)
    scroll_pause_range: tuple[float, float] = (0.3, 1.0)
    typing_delay_range: tuple[float, float] = (0.03, 0.08)
    mouse_move_variance: int = 10

    custom_user_agent: str | None = None
    chromedriver_path: str | None = None

    @property
    def user_agent(self) -> str:
        """Get custom user agent if provided, otherwise get platform-specific default."""
        return self.custom_user_agent if self.custom_user_agent else get_default_user_agent()

    @property
    def chrome_options(self) -> list[str]:
        """Get Chrome options for current platform."""
        return self._get_chrome_options()

    @property
    def chrome_prefs(self) -> dict:
        """Get Chrome preferences."""
        return {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {"images": 1},
            "profile.default_content_settings": {"popups": 0},
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "intl.accept_languages": "en-US,en;q=0.9",
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False,
        }

    @property
    def stealth_script(self) -> str:
        """JavaScript code to bypass detection."""
        return """
        try {
            if (!Object.getOwnPropertyDescriptor(navigator, 'webdriver')) {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
            }
        } catch (e) {}

        try {
            if (!Object.getOwnPropertyDescriptor(navigator, 'plugins')) {
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: {}},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        }
                    ],
                    configurable: true
                });
            }
        } catch (e) {}

        try {
            if (!Object.getOwnPropertyDescriptor(navigator, 'languages')) {
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    configurable: true
                });
            }
        } catch (e) {}

        try {
            const originalQuery = window.navigator.permissions.query;
            if (originalQuery) {
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            }
        } catch (e) {}

        try {
            if (window.chrome && window.chrome.runtime) {
                delete window.chrome.runtime;
            }

            if (!window.chrome) {
                window.chrome = {
                    runtime: undefined
                };
            }
        } catch (e) {}

        try {
            console.debug = () => {};
        } catch (e) {}
        """

    def _get_chrome_options(self) -> list[str]:
        """Get Chrome options based on platform."""
        base_options = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--disable-logging",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI,BlinkGenPropertyTrees",
            "--disable-ipc-flooding-protection",
            "--disable-web-security",
            "--disable-plugins-discovery",
            "--disable-preconnect",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--mute-audio",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--max_old_space_size=4096",
            "--memory-pressure-off",
            "--log-level=3",
            "--silent",
            "--enable-unsafe-swiftshader",
            "--use-gl=swiftshader",
            "--disable-features=VizDisplayCompositor",
            "--disable-site-isolation-trials",
            "--disable-features=BlockInsecurePrivateNetworkRequests",
            "--allow-running-insecure-content",
            "--disable-client-side-phishing-detection",
            # Prevent metrics accumulation to avoid disk space issues
            "--disable-metrics",
            "--disable-metrics-reporting",
            "--disable-crash-reporter",
            "--disk-cache-size=1",
            "--media-cache-size=1",
        ]

        if platform.system() == "Darwin":
            base_options.extend(
                [
                    "--disable-field-trial-config",
                    "--disable-background-media-suspend",
                    "--disable-back-forward-cache",
                    "--disable-features=ImprovedCookieControls,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure",
                    "--disable-component-update",
                    "--disable-domain-reliability",
                    "--disable-breakpad",
                    "--disable-features=MediaRouter",
                    "--no-experiments",
                    "--ignore-gpu-blocklist",
                    "--ignore-certificate-errors",
                    "--ignore-ssl-errors",
                    "--ignore-certificate-errors-spki-list",
                    "--disable-gpu-sandbox",
                    "--disable-software-rasterizer",
                    "--disable-gpu-watchdog",
                    "--hide-scrollbars",
                    "--disable-audio-output",
                    "--no-service-autorun",
                    "--no-wifi",
                    "--no-pings",
                    "--no-zygote",
                    "--password-store=basic",
                    "--use-mock-keychain",
                    "--disable-bundled-ppapi-flash",
                    "--disable-translate",
                    "--safebrowsing-disable-auto-update",
                    "--enable-async-dns",
                    "--force-fieldtrials=*BackgroundTracing/default/",
                ]
            )

        return base_options
