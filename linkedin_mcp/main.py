from linkedin_scraper import LinkedInScraper
from search_filters import SearchFilters
import random
import time

def show_filter_options():
    print("\n📋 Available Filter Options:")
    print("📍 Location Examples:")
    print("   - United States, Canada, United Kingdom, England")
    print("   - Germany, France, Belgium, Spain, Italy")
    print("   - Australia, India, China, Japan, Brazil")
    print("   - Mexico, Netherlands, Singapore, Switzerland")
    print("   - Sweden, South Korea, Russia, UAE")
    
    print("\n🏢 Industry Examples:")
    print("   - Technology, Software Development, Information Technology")
    print("   - Financial Services, Banking, Consulting")
    print("   - Healthcare, Education, Media, Entertainment")
    print("   - Retail, Manufacturing, Real Estate, Energy")
    print("   - Marketing, Sales, Human Resources, Legal")
    print("   - Hospitality, Restaurants, Food & Beverages")
    print("   - Design, E-Learning, Research, Philanthropy")
    print("   - Transportation, Warehousing, Medical Devices")
    print("   - Semiconductors, Industrial Automation, Music")

def enhanced_login_scrape_example():
    EMAIL = "your_email@example.com"
    PASSWORD = "your_password"

    scraper = LinkedInScraper(
        email=EMAIL,
        password=PASSWORD,
        headless=False,
        stealth_mode=True
    )

    try:
        print("\n=== Searching for Python developers (Enhanced Mode) ===")
        filters = SearchFilters(location="San Francisco Bay Area", industry="Technology")
        python_devs = scraper.scrape_search_results("Python developer", max_results=3, filters=filters)
        scraper.save_to_json(python_devs, "enhanced_python_developers.json")

        print(f"\n📈 Scraping Summary:")
        print(f"   Total profiles processed: {len(python_devs)}")
        print(f"   Successful extractions: {len([p for p in python_devs if p.get('name') != 'N/A'])}")

    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        input("\nPress Enter to close browser...")
        scraper.close()

def enhanced_cookie_scrape_example():
    LI_AT_COOKIE = "your_li_at_cookie_value_here"

    scraper = LinkedInScraper(
        li_at_cookie=LI_AT_COOKIE,
        headless=False,
        stealth_mode=True
    )

    try:
        print("\n=== Searching for Data Scientists (Enhanced Mode) ===")
        filters = SearchFilters(location="New York", industry="Financial Services")
        data_scientists = scraper.scrape_search_results("Data Scientist", max_results=2, filters=filters)
        scraper.save_to_json(data_scientists, "enhanced_data_scientists.json")

    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        input("\nPress Enter to close browser...")
        scraper.close()

def enhanced_auto_cookie_example():
    EMAIL = "ak7702401082@gmail.com"
    PASSWORD = "Dramahood2021@"

    scraper = LinkedInScraper(
        email=EMAIL,
        password=PASSWORD,
        headless=False,
        stealth_mode=True
    )

    try:
        queries = ["Golang Developer", "Software Developers", "Product Manager"]

        all_profiles = []
        for i, query in enumerate(queries):
            print(f"\n🔍 Searching for: {query}")
            filters = SearchFilters(location="Remote" if i % 2 == 0 else "United States", 
                                  industry="Technology" if "Developer" in query else "Consulting")
            profiles = scraper.scrape_search_results(query, max_results=2, filters=filters)
            all_profiles.extend(profiles)

            if query != queries[-1]:
                break_time = random.uniform(30, 60)
                print(f"⏸️ Taking a {break_time:.1f} second break between searches...")
                time.sleep(break_time)

        scraper.save_to_json(all_profiles, "enhanced_multi_search_results.json")

        print(f"\n🎯 Final Results:")
        print(f"   Total profiles across all searches: {len(all_profiles)}")
        print(f"   Average profiles per search: {len(all_profiles) / len(queries):.1f}")

    finally:
        scraper.close()

def main():
    print("🚀 Enhanced LinkedIn Scraper with Anti-Detection")
    print("=" * 50)
    print("Choose authentication method:")
    print("1. Email and Password (Enhanced)")
    print("2. li_at Cookie (Enhanced)")
    print("3. Auto Mode (Enhanced - uses saved cookies)")
    print("4. Multiple Search Demo (Enhanced)")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        email = input("Enter your LinkedIn email: ").strip()
        password = input("Enter your LinkedIn password: ").strip()

        scraper = LinkedInScraper(
            email=email,
            password=password,
            headless=False,
            stealth_mode=True
        )

    elif choice == "2":
        cookie = input("Enter your li_at cookie: ").strip()
        scraper = LinkedInScraper(
            li_at_cookie=cookie,
            headless=False,
            stealth_mode=True
        )

    elif choice == "3":
        email = input("Enter your LinkedIn email (for fallback): ").strip()
        password = input("Enter your LinkedIn password (for fallback): ").strip()
        scraper = LinkedInScraper(
            email=email,
            password=password,
            headless=False,
            stealth_mode=True
        )

    elif choice == "4":
        enhanced_auto_cookie_example()
        return

    else:
        print("Invalid choice")
        return

    try:
        query = input("\nEnter search query (e.g., 'Python developer'): ").strip()
        max_results = int(input("Enter max results (e.g., 3): ").strip() or "3")
        
        filters = None
        use_filters = input("\nApply filters? (y/n): ").strip().lower()
        if use_filters == 'y':
            show_filter_options()
            location = input("\nEnter location (optional): ").strip() or None
            industry = input("Enter industry (optional): ").strip() or None
            
            if location or industry:
                filters = SearchFilters(location=location, industry=industry)
                print(f"✅ Filters configured: {filters}")
            else:
                print("ℹ️ No filters applied")

        print(f"\n🎯 Starting enhanced scraping...")
        print(f"   Query: {query}")
        print(f"   Max results: {max_results}")
        if filters and not filters.is_empty():
            print(f"   Filters: {filters}")
        print(f"   Stealth mode: ENABLED")
        print(f"   Human behavior simulation: ENABLED")

        results = scraper.scrape_search_results(query, max_results, filters)
        filename = f"enhanced_{query.replace(' ', '_')}_results.json"
        scraper.save_to_json(results, filename)

        print(f"\n🎉 Scraping completed successfully!")
        print(f"   Profiles found: {len(results)}")
        print(f"   Results saved to: {filename}")
        print(f"   Detection avoidance: ACTIVE")

    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user.")
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    finally:
        input("\n⏳ Press Enter to close browser...")
        scraper.close()

if __name__ == "__main__":
    main()