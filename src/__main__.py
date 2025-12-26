"""Main entry point for the newsletter digest application."""

import sys
import argparse
import unittest
import logging
from pathlib import Path
from datetime import datetime
from src.config import Config
from src.gmail_client import GmailClient
from src.content_extractor import ContentExtractor
from src.summarizer import Summarizer
from src.email_sender import EmailSender

logger = logging.getLogger(__name__)


def run_tests():
    """Run unit and component tests."""
    logger.info("=" * 70)
    logger.info("RUNNING UNIT AND COMPONENT TESTS")
    logger.info("=" * 70)

    # Discover and run all tests
    loader = unittest.TestLoader()
    tests_dir = Path(__file__).parent.parent / 'tests'
    suite = loader.discover(tests_dir, pattern='test_*.py')

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    logger.info("")
    logger.info("=" * 70)
    if result.wasSuccessful():
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 70)
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED")
        logger.info("=" * 70)
        return 1


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
    parser.add_argument('--test', action='store_true',
                       help='Run unit and component tests')
    parser.add_argument('--hours', type=int, default=24,
                       help='Fetch emails from last N hours (default: 24)')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Run tests if --test flag is set
    if args.test:
        return run_tests()

    # Enable preview mode if dry-run is set
    preview_mode = args.dry_run or args.preview

    logger.info("=" * 70)
    logger.info("AI NEWSLETTER DIGEST")
    logger.info("=" * 70)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if preview_mode:
        logger.info("Mode: PREVIEW (no email will be sent)")
    logger.info("=" * 70 + "\n")

    logger.info("Starting newsletter digest workflow")

    try:
        # 1. Load configuration
        logger.info("→ Loading configuration...")
        config = Config()
        logger.info("✓ Configuration loaded\n")

        # 2. Initialize Gmail client
        logger.info("→ Connecting to Gmail API...")
        gmail_client = GmailClient(
            refresh_token=config.gmail_refresh_token,
            client_id=config.gmail_client_id,
            client_secret=config.gmail_client_secret
        )

        # 3. Fetch unread newsletters
        logger.info(f"→ Fetching newsletters from last {args.hours} hours...")
        emails = gmail_client.fetch_unread_emails(
            allowed_senders=config.allowed_senders,
            hours=args.hours
        )

        if not emails:
            logger.info("\n✓ No newsletters to process. Exiting.")
            return 0

        logger.info(f"✓ Found {len(emails)} newsletters to process\n")

        logger.debug("DEBUG: Email subjects:")
        for email in emails:
            logger.debug(f"  - {email.get('subject', 'No subject')}")
        logger.debug("")

        # 4. Extract content from emails
        logger.info("→ Extracting content...")
        extractor = ContentExtractor()
        extracted_items = []

        for email in emails:
            try:
                content = extractor.extract(email)
                extracted_items.append(content)
                logger.debug(f"  ✓ Extracted: {content.get('title', 'Untitled')[:60]}")
            except Exception as e:
                logger.warning(f"Failed to extract from '{email.get('subject', 'Unknown')}': {e}")

        logger.info(f"✓ Extracted content from {len(extracted_items)} newsletters\n")

        if not extracted_items:
            logger.error("✗ No content extracted. Exiting.")
            return 1

        # 5. Summarize with Claude
        logger.info("→ Generating AI summary...")
        summarizer = Summarizer(
            api_key=config.anthropic_api_key,
            model=config.model
        )

        digest_data = summarizer.summarize(
            newsletter_items=extracted_items,
            categories=config.categories,
            max_items_per_category=config.max_items_per_category
        )

        # Count total items in digest
        total_items = sum(len(items) for items in digest_data.values())
        logger.info(f"✓ Digest contains {total_items} items across {len(config.categories)} categories\n")

        logger.debug("DEBUG: Items per category:")
        for category, items in digest_data.items():
            logger.debug(f"  - {category}: {len(items)} items")

        # 6. Send digest email
        logger.info("→ Preparing digest email...")
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

        # 7. Mark emails as read (only if not in preview mode)
        if not preview_mode:
            logger.info("→ Marking newsletters as read...")
            logger.info("Marking newsletters as read")
            email_ids = [email['id'] for email in emails]
            gmail_client.mark_as_read(email_ids)
            logger.info("")

        # Done
        logger.info("=" * 70)
        logger.info("✓ COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Processed: {len(emails)} newsletters")
        logger.info(f"Digest items: {total_items}")
        logger.info("=" * 70)

        logger.info(f"Workflow completed successfully. Processed {len(emails)} newsletters, generated {total_items} digest items")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n✗ Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\n✗ ERROR: {e}", exc_info=args.debug)
        return 1


if __name__ == '__main__':
    sys.exit(main())
