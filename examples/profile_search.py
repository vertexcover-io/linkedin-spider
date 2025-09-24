"""
Example: Profile Search
"""

from linkedin_scraper import LinkedInSpider, ScraperConfig


def search_profiles_example():
    """Example of searching for LinkedIn profiles with filters."""

    config = ScraperConfig(headless=False, page_load_timeout=30)
    # Use either cookie or email and pass.
    # Authentication is usually done once as the session is stored for the further requests.
    scraper = LinkedInSpider(
        email="your_email@example.com",
        password="your_password",
        # li_at_cookie="your_cookie"
        config=config,
    )

    try:
        print("=== Basic Search ===")
        basic_results = scraper.search_profiles(query="software engineer", max_results=5)

        for profile in basic_results:
            print(f"Name: {profile.get('name', 'N/A')}")
            print(f"Headline: {profile.get('headline', 'N/A')}")
            print(f"Location: {profile.get('location', 'N/A')}")
            print("-" * 40)

        print("\n=== Advanced Search with Filters ===")
        filters = {
            "location": "San Francisco Bay Area",
            "current_company": "Google",
            "industry": "Technology",
        }

        filtered_results = scraper.search_profiles(
            query="python developer", max_results=3, filters=filters
        )

        for profile in filtered_results:
            print(f"Name: {profile.get('name', 'N/A')}")
            print(f"Company: {profile.get('company', 'N/A')}")
            print(f"Location: {profile.get('location', 'N/A')}")
            print(f"Profile URL: {profile.get('url', 'N/A')}")
            print("-" * 40)

        filters = {
            "connections": "2nd",
        }
        print("\n=== Search by Connection Level ===")
        connection_results = scraper.search_profiles(
            query="data scientist", filters=filters, max_results=3
        )

        for profile in connection_results:
            print(f"Name: {profile.get('name', 'N/A')}")
            print(f"Headline: {profile.get('headline', 'N/A')}")
            print(f"Connection Level: {profile.get('connection_level', 'N/A')}")
            print("-" * 40)

    except Exception as e:
        print(f"Error during search: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    search_profiles_example()
