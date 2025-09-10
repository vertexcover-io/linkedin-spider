import os
import threading
import weakref
from typing import Optional
from .linkedin_scraper import LinkedInScraper

class LinkedInSessionManager:
    _instance: Optional['LinkedInSessionManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._scraper: Optional[LinkedInScraper] = None
            self._session_active = False
            self._cleanup_refs = []
            self._use_credentials = False
            self._initialized = True
    
    def get_scraper(self) -> LinkedInScraper:
        with self._lock:
            if self._scraper is None or not self._session_active:
                self._initialize_scraper()
            return self._scraper
    
    def _initialize_scraper(self):
        headless = os.getenv('HEADLESS', 'true').lower() in ('true', '1', 'yes')
        print(f"headless: {headless}")
        
        if self._scraper is not None:
            try:
                self._scraper.close()
            except:
                pass
        
        if self._use_credentials:
            email = os.getenv('LINKEDIN_EMAIL')
            password = os.getenv('LINKEDIN_PASSWORD')
            if not email or not password:
                raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables are required when using --login-with-cred")
            
            self._scraper = LinkedInScraper(
                email=email,
                password=password,
                headless=headless,
                stealth_mode=True
            )
        else:
            li_at = os.getenv('cookie')
            if not li_at:
                raise ValueError("cookie environment variable is required")
            
            self._scraper = LinkedInScraper(
                li_at_cookie=li_at,
                headless=headless,
                stealth_mode=True
            )
        
        self._session_active = True
        
        cleanup_ref = weakref.finalize(self._scraper, self._cleanup_scraper)
        self._cleanup_refs.append(cleanup_ref)
    
    def _cleanup_scraper(self):
        self._session_active = False
    
    def is_session_active(self) -> bool:
        if not self._scraper:
            return False
        
        try:
            self._scraper.driver.current_url
            return self._session_active
        except:
            self._session_active = False
            return False
    
    def close_session(self):
        with self._lock:
            if self._scraper:
                try:
                    self._scraper.close()
                except:
                    pass
                finally:
                    self._scraper = None
                    self._session_active = False
    
    def reset_session(self):
        with self._lock:
            self.close_session()
            self._initialize_scraper()
    
    def set_use_credentials(self, use_credentials: bool):
        self._use_credentials = use_credentials
    
    def initialize_session(self):
        """Initialize the LinkedIn session by getting a scraper instance"""
        with self._lock:
            if self._scraper is None or not self._session_active:
                self._initialize_scraper()