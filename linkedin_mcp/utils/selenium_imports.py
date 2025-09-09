"""Common selenium imports used across scrapers."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

__all__ = [
    "By",
    "EC", 
    "TimeoutException",
    "NoSuchElementException",
    "ElementClickInterceptedException", 
    "StaleElementReferenceException",
    "WebDriverException"
]