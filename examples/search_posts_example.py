"""
Example script demonstrating how to search for LinkedIn posts by keywords.

This script shows how to:
1. Initialize the LinkedIn scraper
2. Search for posts using keywords
3. Extract comprehensive post data including author info, content, and engagement metrics
4. Save the results to a JSON file
"""

import os

from linkedin_spider import LinkedinSpider


def main():
    """Search for LinkedIn posts and save results."""
    # Get credentials from environment variables
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    li_at_cookie = os.getenv("LINKEDIN_LI_AT_COOKIE")

    # Initialize the scraper
    print("Initializing LinkedIn scraper...")
    scraper = LinkedinSpider(
        email=email,
        password=password,
        li_at_cookie=li_at_cookie,
    )

    try:
        # Search for posts about "bihar elections"
        keywords = "bihar elections"
        max_results = 10

        print(f"\nSearching for posts with keywords: '{keywords}'")
        print(f"Maximum results: {max_results}")
        print("\nPhase 1: Loading post containers by scrolling...")
        print("Phase 2: Extracting data from loaded posts...\n")

        posts = scraper.search_posts(
            keywords=keywords,
            max_results=max_results,
            scroll_pause=2.0,  # Pause 2 seconds between scrolls
        )

        # Display results
        print(f"\n{'=' * 80}")
        print(f"Found {len(posts)} posts")
        print(f"{'=' * 80}\n")

        for i, post in enumerate(posts, 1):
            print(f"Post #{i}")
            print("-" * 80)
            print(f"Author: {post['author_name']}")
            print(f"Headline: {post['author_headline']}")
            print(f"Profile: {post['author_profile_url']}")
            print(f"Connection: {post['connection_degree']}")
            print(f"Posted: {post['post_time']}")
            print("\nContent:")
            print(
                f"{post['post_text'][:200]}..."
                if len(post["post_text"]) > 200
                else post["post_text"]
            )

            if post["hashtags"]:
                print(f"\nHashtags: {', '.join(post['hashtags'])}")

            print("\nEngagement:")
            print(f"  Likes: {post['likes_count']}")
            print(f"  Comments: {post['comments_count']}")
            print(f"  Reposts: {post['reposts_count']}")

            if post["post_url"] != "N/A":
                print(f"\nPost URL: {post['post_url']}")

            if post["image_url"] != "N/A":
                print("Has image: Yes")

            print("\n")

        # Save to JSON file
        output_file = "linkedin_posts_bihar_elections.json"
        scraper.save_to_json(posts, output_file)
        print(f"Results saved to: {output_file}")

    finally:
        # Close the scraper
        print("\nClosing scraper...")
        scraper.close()


if __name__ == "__main__":
    main()
