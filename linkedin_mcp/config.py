import random

class ScraperConfig:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    HUMAN_DELAY_RANGE = (0.5, 2.0)
    SCROLL_PAUSE_RANGE = (0.3, 1.0)
    TYPING_DELAY_RANGE = (0.03, 0.08)
    MOUSE_MOVE_VARIANCE = 10
    
    CHROME_OPTIONS = [
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
        "--metrics-recording-only",
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
        "--disable-client-side-phishing-detection"
    ]
    
    CHROME_PREFS = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "geolocation": 2,
            "media_stream": 2,
        },
        "profile.managed_default_content_settings": {
            "images": 1
        },
        "profile.default_content_settings": {
            "popups": 0
        },
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "intl.accept_languages": "en-US,en;q=0.9",
        "webrtc.ip_handling_policy": "disable_non_proxied_udp",
        "webrtc.multiple_routes_enabled": False,
        "webrtc.nonproxied_udp_enabled": False
    }
    
    STEALTH_SCRIPT = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

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
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );

        if (window.chrome && window.chrome.runtime) {
            delete window.chrome.runtime;
        }

        window.chrome = {
            runtime: undefined
        };

        console.debug = () => {};
    """
    
    @classmethod
    def get_random_user_agent(cls):
        return random.choice(cls.USER_AGENTS)