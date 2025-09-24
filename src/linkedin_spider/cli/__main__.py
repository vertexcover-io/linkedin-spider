#!/usr/bin/env python3
"""CLI entry point."""

import sys

def main():
    """Main entry point for CLI."""
    try:
        from linkedin_spider.cli.main import app
        app()
    except ImportError as e:
        if "cyclopts" in str(e):
            print("CLI functionality requires the 'cli' extra. Install with:")
            print("pip install linkedin-spider[cli]")
            sys.exit(1)
        raise

if __name__ == "__main__":
    main()