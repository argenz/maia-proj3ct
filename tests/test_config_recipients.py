"""Unit tests for Config digest_recipients property."""

import unittest
from unittest.mock import patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigDigestRecipients(unittest.TestCase):
    """Test the digest_recipients configuration property."""

    @patch.dict('os.environ', {
        'ANTHROPIC_API_KEY': 'test_key',
        'GMAIL_REFRESH_TOKEN': 'test_token',
        'GMAIL_CLIENT_ID': 'test_client_id',
        'GMAIL_CLIENT_SECRET': 'test_secret',
        'GMAIL_NEWSLETTER_ACCOUNT': 'newsletter@example.com',
        'GMAIL_DIGEST_RECIPIENT': 'single@example.com',
    })
    def test_single_recipient_fallback(self):
        """Test fallback to single recipient when GMAIL_DIGEST_RECIPIENTS not set."""
        from src.config import Config
        config = Config()
        
        recipients = config.digest_recipients
        self.assertEqual(recipients, ['single@example.com'])

    @patch.dict('os.environ', {
        'ANTHROPIC_API_KEY': 'test_key',
        'GMAIL_REFRESH_TOKEN': 'test_token',
        'GMAIL_CLIENT_ID': 'test_client_id',
        'GMAIL_CLIENT_SECRET': 'test_secret',
        'GMAIL_NEWSLETTER_ACCOUNT': 'newsletter@example.com',
        'GMAIL_DIGEST_RECIPIENT': 'single@example.com',
        'GMAIL_DIGEST_RECIPIENTS': 'user1@example.com,user2@example.com,user3@example.com',
    })
    def test_multiple_recipients(self):
        """Test parsing multiple recipients from comma-separated list."""
        from src.config import Config
        config = Config()
        
        recipients = config.digest_recipients
        self.assertEqual(recipients, ['user1@example.com', 'user2@example.com', 'user3@example.com'])

    @patch.dict('os.environ', {
        'ANTHROPIC_API_KEY': 'test_key',
        'GMAIL_REFRESH_TOKEN': 'test_token',
        'GMAIL_CLIENT_ID': 'test_client_id',
        'GMAIL_CLIENT_SECRET': 'test_secret',
        'GMAIL_NEWSLETTER_ACCOUNT': 'newsletter@example.com',
        'GMAIL_DIGEST_RECIPIENT': 'single@example.com',
        'GMAIL_DIGEST_RECIPIENTS': '  user1@example.com , user2@example.com  ',
    })
    def test_multiple_recipients_with_whitespace(self):
        """Test that whitespace is stripped from recipients."""
        from src.config import Config
        config = Config()
        
        recipients = config.digest_recipients
        self.assertEqual(recipients, ['user1@example.com', 'user2@example.com'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
