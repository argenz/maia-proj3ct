"""Main entry point for the newsletter digest application."""

import sys
import argparse
from datetime import datetime
from src.config import Config
from src.gmail_client import GmailClient
from src.content_extractor import ContentExtractor
from src.summarizer import Summarizer
from src.email_sender import EmailSender


def main():
    """Main application workflow."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='AI Newsletter Digest Generator')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without sending email (preview mode)')
    parser.add_argument('--preview', action='store_true',
                       help='Print digest to console instead of sending')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output')
    parser.add_argument('--hours', type=int, default=24,
                       help='Fetch emails from last N hours (default: 24)')

    args = parser.parse_args()

    # Enable preview mode if dry-run is set
    preview_mode = args.dry_run or args.preview

    print("=" * 70)
    print("AI NEWSLETTER DIGEST")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if preview_mode:
        print("Mode: PREVIEW (no email will be sent)")
    print("=" * 70 + "\n")

    try:
        # 1. Load configuration
        print("→ Loading configuration...")
        config = Config()
        print("✓ Configuration loaded\n")

        # 2. Initialize Gmail client
        print("→ Connecting to Gmail API...")
        gmail_client = GmailClient(
            refresh_token=config.gmail_refresh_token,
            client_id=config.gmail_client_id,
            client_secret=config.gmail_client_secret
        )
        print()

        # 3. Fetch unread newsletters
        print(f"→ Fetching newsletters from last {args.hours} hours...")
        emails = gmail_client.fetch_unread_emails(
            allowed_senders=config.allowed_senders,
            hours=args.hours
        )

        if not emails:
            print("\n✓ No newsletters to process. Exiting.")
            return 0

        print(f"✓ Found {len(emails)} newsletters to process\n")

        if args.debug:
            print("DEBUG: Email subjects:")
            for email in emails:
                print(f"  - {email.get('subject', 'No subject')}")
            print()

        # 4. Extract content from emails
        print("→ Extracting content...")
        extractor = ContentExtractor()
        extracted_items = []

        for email in emails:
            try:
                content = extractor.extract(email)
                extracted_items.append(content)
                if args.debug:
                    print(f"  ✓ Extracted: {content.get('title', 'Untitled')[:60]}")
            except Exception as e:
                print(f"  ⚠ Failed to extract from '{email.get('subject', 'Unknown')}': {e}")

        print(f"✓ Extracted content from {len(extracted_items)} newsletters\n")

        if not extracted_items:
            print("✗ No content extracted. Exiting.")
            return 1

        # 5. Summarize with Claude
        print("→ Generating AI summary...")
        summarizer = Summarizer(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        digest_data = summarizer.summarize(
            newsletter_items=extracted_items,
            categories=config.categories,
            max_items_per_category=config.max_items_per_category
        )
        print()

        # Count total items in digest
        total_items = sum(len(items) for items in digest_data.values())
        print(f"✓ Digest contains {total_items} items across {len(config.categories)} categories\n")

        if args.debug:
            print("DEBUG: Items per category:")
            for category, items in digest_data.items():
                print(f"  - {category}: {len(items)} items")
            print()

        # 6. Send digest email
        print("→ Preparing digest email...")
        email_sender = EmailSender(
            refresh_token=config.gmail_refresh_token,
            client_id=config.gmail_client_id,
            client_secret=config.gmail_client_secret,
            from_email=config.newsletter_account
        )

        email_sender.send_digest(
            to_email=config.digest_recipient,
            digest_data=digest_data,
            total_newsletters=len(emails),
            preview_only=preview_mode
        )
        print()

        # 7. Mark emails as read (only if not in preview mode)
        if not preview_mode:
            print("→ Marking newsletters as read...")
            email_ids = [email['id'] for email in emails]
            gmail_client.mark_as_read(email_ids)
            print()

        # Done
        print("=" * 70)
        print("✓ COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Processed: {len(emails)} newsletters")
        print(f"Digest items: {total_items}")
        print("=" * 70)

        return 0

    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        return 130

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
