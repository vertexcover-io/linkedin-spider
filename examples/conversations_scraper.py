"""
Example: Conversations Scraping
"""

import asyncio

from linkedin_scraper import LinkedinSpider, ScraperConfig


async def scrape_conversations_list_example():
    """Example of scraping your LinkedIn conversations list."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)
    try:
        print("=== Your Conversations ===")
        conversations = scraper.scrape_conversations_list(max_results=10)

        print(conversations)

        for conversation in conversations:
            print(f"Participant: {conversation.get('participant_name', 'N/A')}")
            print(f"Last Message: {conversation.get('message_snippet', 'N/A')[:100]}...")
            print(f"Timestamp: {conversation.get('timestamp', 'N/A')}")
            print(f"Status: {conversation.get('online_status','N/A')}")
            print(f"IsSponsored: {conversation.get('is_sponsored', False)}")
            print("-" * 40)

    except Exception as e:
        print(f"Error scraping conversations list: {e}")

    finally:
        scraper.close()


async def scrape_specific_conversation_example():
    """Example of scraping a specific conversation."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        participant_name = "Eric"

        print(f"=== Conversation with {participant_name} ===")

        data = scraper.scrape_conversation_messages(participant_name=participant_name)

        if data.get("messages"):
            for message in data["messages"]:
                if isinstance(message, dict):
                    sender_name = message.get("sender_name", "Unknown")
                    sender_profile_url = message.get("sender_profile_url", "N/A")
                    sender_profile_image = message.get("sender_profile_image", "N/A")
                    is_premium = message.get("is_premium", False)
                    is_verified = message.get("is_verified", False)
                    pronouns = message.get("pronouns", "N/A")
                    timestamp = message.get("timestamp", "No timestamp")
                    message_text = message.get("message_text", "No content")
                    attachments = message.get("attachments", [])
                    message_urn = message.get("message_urn", "N/A")

                    print(f"[{timestamp}] {sender_name}")
                    print(f"Profile URL: {sender_profile_url}")
                    print(f"Profile Image: {sender_profile_image}")
                    print(f"Premium: {is_premium}, Verified: {is_verified}, Pronouns: {pronouns}")
                    print(f"Message: {message_text}")
                    print(f"Attachments: {attachments}")
                    print(f"URN: {message_urn}")
                    print("-" * 60)
        else:
            print("No messages found")

    except Exception as e:
        print(f"Error scraping conversation: {e}")

    finally:
        scraper.close()


async def export_all_conversations_example():
    """Example of exporting all conversations to files."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        print("=== Exporting All Conversations ===")

        conversations = scraper.scrape_conversations_list(max_results=50)

        for idx, conversation in enumerate(conversations):
            participant_name = conversation.get("participant_name", f"Unknown_{idx}")
            print(f"Exporting conversation with {participant_name}...")

            try:
                data = scraper.scrape_conversation_messages(participant_name=participant_name)

                if data.get("messages"):
                    safe_name = "".join(
                        c for c in participant_name if c.isalnum() or c in (" ", "-", "_")
                    ).rstrip()
                    filename = f"conversation_{safe_name}.txt"

                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"Conversation with {participant_name}\n")
                        f.write("=" * 50 + "\n\n")

                        for message in data["messages"]:
                            if not isinstance(message, dict):
                                continue
                            sender = message.get("sender_name", "Unknown")
                            timestamp = message.get("timestamp", "No timestamp")
                            text = message.get("message_text", "No content")
                            profile_url = message.get("sender_profile_url", "N/A")
                            is_premium = message.get("is_premium", False)
                            is_verified = message.get("is_verified", False)
                            pronouns = message.get("pronouns", "N/A")
                            attachments = message.get("attachments", [])
                            urn = message.get("message_urn", "N/A")

                            f.write(f"[{timestamp}] {sender}\n")
                            f.write(f"Profile: {profile_url}\n")
                            f.write(
                                f"Premium: {is_premium}, Verified: {is_verified}, Pronouns: {pronouns}\n"
                            )
                            f.write(f"Message: {text}\n")
                            f.write(f"Attachments: {attachments}\n")
                            f.write(f"URN: {urn}\n")
                            f.write("-" * 50 + "\n\n")

                    print(f"✓ Exported to {filename}")
                else:
                    print(f"✗ No messages found for {participant_name}")

                await asyncio.sleep(1)

            except Exception as e:
                print(f"✗ Error exporting conversation with {participant_name}: {e}")

        print("Export completed!")

    except Exception as e:
        print(f"Error during export: {e}")

    finally:
        scraper.close()


async def search_conversations_example():
    """Example of searching through conversations for specific keywords."""

    config = ScraperConfig(headless=True, page_load_timeout=30)
    scraper = LinkedinSpider(config)

    try:
        search_keywords = ["meeting", "project", "opportunity"]

        print("=== Searching Conversations ===")

        conversations = scraper.scrape_conversations_list(max_results=20)

        for conversation in conversations:
            participant_name = conversation.get("participant_name", "Unknown")

            try:
                data = scraper.scrape_conversation_messages(participant_name=participant_name)

                if "messages" not in data or not data["messages"]:
                    continue

                matching_messages = []
                for message in data["messages"]:
                    if not isinstance(message, dict):
                        continue
                    content = message.get("message_text", "").lower()
                    for keyword in search_keywords:
                        if keyword in content:
                            matching_messages.append(message)
                            break

                if matching_messages:
                    print(
                        f"\n--- Found {len(matching_messages)} matching messages with {participant_name} ---"
                    )
                    for message in matching_messages[:3]:
                        print(
                            f"[{message.get('timestamp', 'N/A')}] "
                            f"{message.get('sender_name', 'Unknown')}: "
                            f"{message.get('message_text', 'No content')[:100]}..."
                        )

                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error searching conversation with {participant_name}: {e}")

    except Exception as e:
        print(f"Error during conversation search: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    print("Running conversations list example...")
    asyncio.run(scrape_conversations_list_example())

    print("\n\nRunning specific conversation example...")
    asyncio.run(scrape_specific_conversation_example())

    print("\n\nRunning export all conversations example...")
    asyncio.run(export_all_conversations_example())

    print("\n\nRunning search conversations example...")
    asyncio.run(search_conversations_example())
