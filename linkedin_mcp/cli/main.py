from ..core import LinkedInScraper
from ..scrapers import SearchFilters
from cyclopts import App
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = App()

@app.command()
def scrape(
    query: str,
    max_results: int = 3,
    location: str = None,
    industry: str = None,
    current_company: str = None,
    connections: str = None,
    connection_of: str = None,
    followers_of: str = None,
    headless: bool = False
):
    """Scrape LinkedIn profiles based on search query."""
    li_at = os.getenv('cookie')
    if not li_at:
        raise ValueError("cookie environment variable is required")

    scraper = LinkedInScraper(
        li_at_cookie=li_at,
        headless=headless,
        stealth_mode=True
    )

    try:
        filters = None
        if location or industry or current_company or connections or connection_of or followers_of:
            filters = SearchFilters(
                location=location,
                industry=industry,
                current_company=current_company,
                connections=connections,
                connection_of=connection_of,
                followers_of=followers_of
            )

        results = scraper.scrape_search_results(query, max_results, filters)

        print(json.dumps(results, indent=2))

    except KeyboardInterrupt:
        print("Scraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        scraper.close()

@app.command()
def profile(
    profile_url: str,
    headless: bool = False
):
    """Scrape a single LinkedIn profile."""
    li_at = os.getenv('cookie')
    if not li_at:
        raise ValueError("cookie environment variable is required")

    scraper = LinkedInScraper(
        li_at_cookie=li_at,
        headless=headless,
        stealth_mode=True
    )

    try:
        result = scraper.scrape_profile(profile_url)

        print(json.dumps(result, indent=2))

    except KeyboardInterrupt:
        print("Scraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    app()
