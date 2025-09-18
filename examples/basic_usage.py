"""
Example: Basic Usage
A simple getting started example for the LinkedIn Scraper.
"""

from linkedin_scraper import LinkedInScraper, ScraperConfig


def basic_example():
    """Basic example showing the essential workflow."""

    config = ScraperConfig(headless=True, page_load_timeout=30)

    # Use either cookie or email and pass.
    # Authentication is usually done once as the session is stored for the further requests.
    scraper = LinkedInScraper(
        email="your_email@example.com",
        password="your_password",
        # li_at_cookie="your_linkedin_cookie",
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
