"""
Example: Basic Usage
"""

import os

from linkedin_spider import LinkedinSpider, ScraperConfig


def basic_example():
    """Basic example showing the essential workflow."""

    config = ScraperConfig(headless=True, page_load_timeout=30)

    # Option 1: Use saved cookies (run `linkedin-spider-cli login` first)
    # Option 2: Use li_at cookie directly
    scraper = LinkedinSpider(
        li_at_cookie=os.getenv("LINKEDIN_COOKIE"),
        config=config,
    )

    try:
        print("Searching for profiles...")
        results = scraper.search_profiles(query="software engineer", max_results=3)

        print(f"\nFound {len(results)} profiles:")
        for i, profile in enumerate(results, 1):
            print(f"{i}. {profile.get('name', 'N/A')} - {profile.get('headline', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        print("Closing scraper...")
        scraper.close()


if __name__ == "__main__":
    print("LinkedIn Scraper - Basic Usage Example")
    print("=" * 40)
    basic_example()
