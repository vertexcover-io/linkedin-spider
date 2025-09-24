#!/usr/bin/env python3
"""LinkedIn Scraper CLI application."""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from dotenv import load_dotenv

from linkedin_scraper import LinkedInSpider, ScraperConfig

load_dotenv()

app = App(
    name="linkedin-spider", help="LinkedIn Spider - Extract LinkedIn profile and company data."
)


@app.command
def search(
    query: Annotated[str, Parameter(name=["-q", "--query"], help="Search query for profiles")],
    max_results: Annotated[
        int, Parameter(name=["-n", "--max-results"], help="Maximum number of results")
    ] = 5,
    output: Annotated[
        str | None,
        Parameter(name=["-o", "--output"], help="Output file path (.json or .csv format)"),
    ] = None,
    headless: bool | None = None,
    email: Annotated[str | None, Parameter(help="LinkedIn email for authentication")] = None,
    password: Annotated[str | None, Parameter(help="LinkedIn password for authentication")] = None,
    cookie: Annotated[
        str | None, Parameter(help="LinkedIn li_at cookie for authentication")
    ] = None,
):
    """Search for LinkedIn profiles."""
    try:
        config = _create_config(headless)
        credentials = _get_credentials(email, password, cookie)

        scraper = LinkedInSpider(
            email=credentials.get("email"),
            password=credentials.get("password"),
            li_at_cookie=credentials.get("cookie"),
            config=config,
        )

        results = scraper.search_profiles(query, max_results)

        if output:
            _save_results(results, output)
            print(f"Results saved to {output}")
        else:
            print(json.dumps(results, indent=2))

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)
    finally:
        if "scraper" in locals():
            scraper.close()


@app.command
def profile(
    url: Annotated[str, Parameter(name=["-u", "--url"], help="LinkedIn profile URL")],
    output: Annotated[
        str | None,
        Parameter(name=["-o", "--output"], help="Output file path (.json or .csv format)"),
    ] = None,
    headless: bool | None = None,
    email: Annotated[str | None, Parameter(help="LinkedIn email for authentication")] = None,
    password: Annotated[str | None, Parameter(help="LinkedIn password for authentication")] = None,
    cookie: Annotated[
        str | None, Parameter(help="LinkedIn li_at cookie for authentication")
    ] = None,
):
    """Scrape a specific LinkedIn profile."""
    try:
        config = _create_config(headless)
        credentials = _get_credentials(email, password, cookie)

        scraper = LinkedInSpider(
            email=credentials.get("email"),
            password=credentials.get("password"),
            li_at_cookie=credentials.get("cookie"),
            config=config,
        )

        result = scraper.scrape_profile(url)

        if result:
            if output:
                _save_results(result, output)
                print(f"Profile data saved to {output}")
            else:
                print(json.dumps(result, indent=2))
        else:
            print("Failed to scrape profile", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)
    finally:
        if "scraper" in locals():
            scraper.close()


@app.command
def company(
    url: Annotated[str, Parameter(name=["-u", "--url"], help="LinkedIn company URL")],
    output: Annotated[
        str | None,
        Parameter(name=["-o", "--output"], help="Output file path (.json or .csv format)"),
    ] = None,
    headless: bool | None = None,
    email: Annotated[str | None, Parameter(help="LinkedIn email for authentication")] = None,
    password: Annotated[str | None, Parameter(help="LinkedIn password for authentication")] = None,
    cookie: Annotated[
        str | None, Parameter(help="LinkedIn li_at cookie for authentication")
    ] = None,
):
    """Scrape a LinkedIn company page."""
    try:
        config = _create_config(headless)
        credentials = _get_credentials(email, password, cookie)

        scraper = LinkedInSpider(
            email=credentials.get("email"),
            password=credentials.get("password"),
            li_at_cookie=credentials.get("cookie"),
            config=config,
        )

        result = scraper.scrape_company(url)

        if result:
            if output:
                _save_results(result, output)
                print(f"Company data saved to {output}")
            else:
                print(json.dumps(result, indent=2))
        else:
            print("Failed to scrape company", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)
    finally:
        if "scraper" in locals():
            scraper.close()


@app.command
def connections(
    max_results: Annotated[
        int, Parameter(name=["-n", "--max-results"], help="Maximum number of results")
    ] = 10,
    output: Annotated[
        str | None,
        Parameter(name=["-o", "--output"], help="Output file path (.json or .csv format)"),
    ] = None,
    headless: bool | None = None,
    email: Annotated[str | None, Parameter(help="LinkedIn email for authentication")] = None,
    password: Annotated[str | None, Parameter(help="LinkedIn password for authentication")] = None,
    cookie: Annotated[
        str | None, Parameter(help="LinkedIn li_at cookie for authentication")
    ] = None,
):
    """Scrape incoming connection requests."""
    try:
        config = _create_config(headless)
        credentials = _get_credentials(email, password, cookie)

        scraper = LinkedInSpider(
            email=credentials.get("email"),
            password=credentials.get("password"),
            li_at_cookie=credentials.get("cookie"),
            config=config,
        )

        results = scraper.scrape_incoming_connections(max_results)

        if output:
            _save_results(results, output)
            print(f"Connection data saved to {output}")
        else:
            print(json.dumps(results, indent=2))

    except Exception as e:
        print(f"Error: {e!s}", file=sys.stderr)
        sys.exit(1)
    finally:
        if "scraper" in locals():
            scraper.close()


def _create_config(headless: bool | None) -> ScraperConfig:
    """Create scraper configuration."""
    if headless is None:
        headless = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

    return ScraperConfig(headless=headless)


def _get_credentials(email: str | None, password: str | None, cookie: str | None) -> dict:
    """Get authentication credentials from arguments or environment."""
    credentials = {
        "email": email or os.getenv("LINKEDIN_EMAIL"),
        "password": password or os.getenv("LINKEDIN_PASSWORD"),
        "cookie": cookie or os.getenv("LINKEDIN_COOKIE") or os.getenv("cookie"),
    }

    if not any(credentials.values()):
        raise ValueError(
            "Authentication required. Provide either:\n"
            "1. Email and password (--email, --password)\n"
            "2. LinkedIn cookie (--cookie)\n"
            "3. Set environment variables: LINKEDIN_EMAIL, LINKEDIN_PASSWORD, or LINKEDIN_COOKIE"
        )

    return credentials


def _save_results(data, output_path: str) -> None:
    """Save results to JSON or CSV file based on extension."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.suffix.lower() == ".csv":
        _save_as_csv(data, output_file)
    else:
        _save_as_json(data, output_file)


def _save_as_json(data, output_file: Path) -> None:
    """Save data as JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_as_csv(data, output_file: Path) -> None:
    """Save data as CSV file."""
    if not data:
        return

    if isinstance(data, list):
        if not data[0]:
            return

        if isinstance(data[0], dict):
            fieldnames = data[0].keys()
        else:
            fieldnames = ["value"]
            data = [{"value": item} for item in data]
    elif isinstance(data, dict):
        fieldnames = data.keys()
        data = [data]
    else:
        fieldnames = ["value"]
        data = [{"value": data}]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    app()
