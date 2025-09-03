from linkedin_scraper import LinkedInScraper
from search_filters import SearchFilters
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description='LinkedIn Scraper')
    parser.add_argument('--li-at', required=True, help='LinkedIn li_at cookie')
    parser.add_argument('--query', required=True, help='Search query')
    parser.add_argument('--max-results', type=int, default=3, help='Maximum results')
    parser.add_argument('--location', help='Location filter')
    parser.add_argument('--industry', help='Industry filter')
    
    args = parser.parse_args()
    
    scraper = LinkedInScraper(
        li_at_cookie=args.li_at,
        headless=False,
        stealth_mode=True
    )
    
    try:
        filters = None
        if args.location or args.industry:
            filters = SearchFilters(location=args.location, industry=args.industry)
        
        results = scraper.scrape_search_results(args.query, args.max_results, filters)
        
        print(json.dumps(results, indent=2))
        
    except KeyboardInterrupt:
        print("Scraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()