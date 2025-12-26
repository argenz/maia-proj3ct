#!/usr/bin/env python3
"""Test Gmail API access with the obtained credentials."""

import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.gmail_client import GmailClient


def main():
    """Test Gmail API connection."""
    print("=" * 70)
    print("GMAIL API CONNECTION TEST")
    print("=" * 70)
    print()

    try:
        # Load configuration
        print("→ Loading configuration from .env...")
        config = Config()
        print("✓ Configuration loaded")
        print()

        # Test Gmail connection
        print("→ Connecting to Gmail API...")
        gmail_client = GmailClient(
            refresh_token=config.gmail_refresh_token,
            client_id=config.gmail_client_id,
            client_secret=config.gmail_client_secret
        )
        print()

        # Fetch recent emails (just to test)
        print("→ Fetching recent emails (test)...")
        emails = gmail_client.fetch_unread_emails(
            allowed_senders=config.allowed_senders,
            hours=168  # Last 7 days
        )
        print()

        # Results
        print("=" * 70)
        print("✓ SUCCESS!")
        print("=" * 70)
        print(f"Gmail API connection working!")
        print(f"Found {len(emails)} unread newsletter emails in the last 7 days")
        print()

        if emails:
            print("Recent newsletters:")
            for i, email in enumerate(emails[:5], 1):
                print(f"{i}. {email.get('subject', 'No subject')}")
                print(f"   From: {email.get('from', 'Unknown')}")
            if len(emails) > 5:
                print(f"   ... and {len(emails) - 5} more")
        print()
        print("You're ready to run the full application!")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("✗ ERROR")
        print("=" * 70)
        print(f"{e}")
        print()
        print("Make sure:")
        print("- You've completed the OAuth setup (python scripts/oauth_setup.py)")
        print("- Your .env file has the correct credentials")
        print("- The Gmail API is enabled in Google Cloud Console")
        print()
        return 1


if __name__ == '__main__':
    exit(main())
