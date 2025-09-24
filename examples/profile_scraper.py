"""
Example: Profile Scraping
"""

from linkedin_spider import LinkedinSpider, ScraperConfig


def scrape_profile_example():
    """Example of scraping a single LinkedIn profile."""

    config = ScraperConfig(
        headless=False,
        page_load_timeout=30,
    )

    # Use either cookie or email and pass.
    # Authentication is usually done once as the session is stored for the further requests.
    scraper = LinkedinSpider(
        email="your_email@example.com", password="your_password", config=config
    )
    try:
        profile_url = "https://www.linkedin.com/in/demo-account/"
        print(f"Scraping profile: {profile_url}")
        profile_data = scraper.scrape_profile(profile_url)

        if profile_data:
            if isinstance(profile_data, dict):
                print(f"Name: {profile_data.get('name', 'N/A')}")
                print(f"Headline: {profile_data.get('headline', 'N/A')}")
                print(f"Location: {profile_data.get('location', 'N/A')}")
                print(f"Company: {profile_data.get('company', 'N/A')}")
                print(f"Connections: {profile_data.get('connections', 'N/A')}")

                if profile_data.get("experience"):
                    print("\nExperience:")
                    for exp in profile_data["experience"]:
                        print(f"- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
                        print(f"  {exp.get('duration', 'N/A')} | {exp.get('location', 'N/A')}")
                        print(f"  Company URL: {exp.get('company_url', 'N/A')}\n")

                if profile_data.get("education"):
                    print("\nEducation:")
                    for edu in profile_data["education"]:
                        print(
                            f"- {edu.get('degree', 'N/A')} in {edu.get('field_of_study', 'N/A')} "
                            f"at {edu.get('school', 'N/A')}"
                        )
                        print(
                            f"  {edu.get('duration', 'N/A')} | Grade: {edu.get('grade', 'N/A')}\n"
                        )

            elif isinstance(profile_data, list):
                print("\nExperience:")
                for exp in profile_data:
                    print(f"- {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}")
                    print(f"  {exp.get('duration', 'N/A')} | {exp.get('location', 'N/A')}")
                    print(f"  Company URL: {exp.get('company_url', 'N/A')}\n")

            else:
                print("Unrecognized profile_data format")
        else:
            print("No profile data found")

    except Exception as e:
        print(f"Error scraping profile: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    scrape_profile_example()
