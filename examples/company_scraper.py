"""
Example: Company Scraping
"""

from linkedin_scraper import LinkedinSpider, ScraperConfig


def scrape_company_example():
    """Example of scraping LinkedIn company pages."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        companies = [
            "https://www.linkedin.com/company/google/",
            "https://www.linkedin.com/company/microsoft/",
            "https://www.linkedin.com/company/apple/",
        ]

        for company_url in companies:
            print(f"\n=== Scraping Company: {company_url} ===")

            try:
                company_data = scraper.scrape_company(company_url)
                print(f"Name: {company_data.get('name', 'N/A')}")
                print(f"Industry: {company_data.get('industry', 'N/A')}")
                print(f"Size: {company_data.get('company_size', 'N/A')}")
                print(f"Headquarters: {company_data.get('headquarters', 'N/A')}")
                print(f"Founded: {company_data.get('founded', 'N/A')}")
                print(f"Website: {company_data.get('website', 'N/A')}")
                print(f"Followers: {company_data.get('followers', 'N/A')}")
                print(f"Description: {company_data.get('description', 'N/A')[:200]}...")

                specialties = company_data.get("specialties", [])
                if specialties:
                    print(f"Specialties: {', '.join(specialties)}")

            except Exception as e:
                print(f"Error scraping {company_url}: {e}")

            print("-" * 60)

    except Exception as e:
        print(f"Error during company scraping: {e}")

    finally:
        scraper.close()


def search_profiles_example():
    """Example of searching for profiles with company filter."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        print("=== Searching for Profiles at AI Companies ===")

        search_results = scraper.search_profiles(
            query="artificial intelligence engineer",
            max_results=5,
            filters={"current_company": "Google"},
        )
        print(search_results)

        for profile in search_results:
            print(f"Name: {profile.get('name', 'N/A')}")
            print(f"Title: {profile.get('headline', 'N/A')}")
            print(f"Location: {profile.get('location', 'N/A')}")
            print(f"Profile URL: {profile.get('profile_url', 'N/A')}")
            print(f"Profole Photo: {profile.get('image_url',"N/A")}")
            print("-" * 40)

    except Exception as e:
        print(f"Error during profile search: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    print("Running company scraping example...")
    scrape_company_example()

    print("\n\nRunning profile search example...")
    search_profiles_example()
