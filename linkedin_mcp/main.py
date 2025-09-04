from linkedin_scraper import LinkedInScraper
from search_filters import SearchFilters
from cyclopts import App
import json

app = App()

@app.command()
def scrape(
    li_at: str,
    query: str,
    max_results: int = 3,
    location: str = None,
    industry: str = None,
    headless: bool = False
):
    """Scrape LinkedIn profiles based on search query."""
    scraper = LinkedInScraper(
        li_at_cookie=li_at,
        headless=headless,
        stealth_mode=True
    )
    
    try:
        filters = None
        if location or industry:
            filters = SearchFilters(location=location, industry=industry)
        
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
    li_at: str,
    profile_url: str,
    headless: bool = False
):
    """Scrape a single LinkedIn profile."""
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