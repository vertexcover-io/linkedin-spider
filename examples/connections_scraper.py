"""
Example: Connections Scraping
"""

import asyncio

from linkedin_spider import LinkedinSpider, ScraperConfig


async def scrape_connections_example():
    """Example of scraping your LinkedIn connections."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        print("=== Your Connections ===")
        connections = scraper.scrape_outgoing_connections(max_results=10)

        for connection in connections:
            print(f"Name: {connection.get('name', 'N/A')}")
            print(f"Message: {connection.get('message', 'N/A')}")
            print(f"Sent Time: {connection.get('time_sent', 'N/A')}")
            print(f"Profile URL: {connection.get('profile_url', 'N/A')}")
            print("-" * 40)

        print("\n=== Incoming Connection Requests ===")
        incoming_requests = scraper.scrape_incoming_connections(max_results=5)

        if incoming_requests:
            for request in incoming_requests:
                print(f"Name: {request.get('name', 'N/A')}")
                print(f"Headline: {request.get('headline', 'N/A')}")
                print(f"Message: {request.get('message', 'N/A')}")
                print(f"Sent On: {request.get('sent_date', 'N/A')}")
                print("-" * 40)
        else:
            print("No pending connection requests found.")

    except Exception as e:
        print(f"Error scraping connections: {e}")

    finally:
        scraper.close()


async def send_connection_request_example():
    """Example of sending a connection request."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        profile_url = "https://www.linkedin.com/in/akto/"

        message = "Hi! I'd like to connect with you. I'm interested in your work in AI/ML."
        print(f"Sending connection request to: {profile_url}")

        result = scraper.send_connection_request(profile_url=profile_url, note=message)

        if result.get("success"):
            print("Connection request sent successfully!")
        else:
            print(f"Failed to send connection request: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error sending connection request: {e}")

    finally:
        await scraper.close()


async def bulk_connection_requests_example():
    """Example of sending multiple connection requests."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)
    try:
        profiles_to_connect = [
            {
                "url": "https://www.linkedin.com/in/profile1/",
                "message": "Hi! I'd love to connect and learn about your experience.",
            },
            {
                "url": "https://www.linkedin.com/in/profile2/",
                "message": "Hello! I'm interested in connecting with fellow professionals.",
            },
        ]

        print("=== Sending Bulk Connection Requests ===")

        for profile in profiles_to_connect:
            try:
                result = await scraper.send_connection_request(
                    profile_url=profile["url"], note=profile["message"]
                )

                if result.get("success"):
                    print(f"✓ Sent request to {profile['url']}")
                else:
                    print(f"✗ Failed to send request to {profile['url']}: {result.get('error')}")

                await asyncio.sleep(2)

            except Exception as e:
                print(f"✗ Error sending request to {profile['url']}: {e}")

    except Exception as e:
        print(f"Error in bulk connection requests: {e}")

    finally:
        await scraper.close()


if __name__ == "__main__":
    print("\n\nRunning connection request example...")
    asyncio.run(send_connection_request_example())

    print("\n\nRunning bulk connection requests example...")
