"""Unit tests for EmailSender."""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_sender import EmailSender


class TestEmailSender(unittest.TestCase):
    """Test the EmailSender class."""

    @patch('src.email_sender.build')
    @patch('src.email_sender.Credentials')
    def test_initialization(self, mock_creds, mock_build):
        """Test EmailSender initialization."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        sender = EmailSender(
            refresh_token='test_token',
            client_id='test_client_id',
            client_secret='test_secret',
            from_email='test@example.com'
        )

        self.assertEqual(sender.from_email, 'test@example.com')
        self.assertIsNotNone(sender.service)

    @patch('src.email_sender.build')
    @patch('src.email_sender.Credentials')
    def test_generate_text_digest(self, mock_creds, mock_build):
        """Test generating plain text digest."""
        sender = EmailSender('token', 'client_id', 'secret', 'from@example.com')

        digest_data = {
            'Papers': [
                {
                    'title': 'Research Paper Title',
                    'summary': 'This is a summary of the research paper.',
                    'source': 'Academic Journal',
                    'link': 'https://example.com/paper'
                }
            ],
            'News': [
                {
                    'title': 'Industry News',
                    'summary': 'Latest developments in AI.',
                    'source': 'Tech News',
                    'link': ''
                }
            ],
            'Tools': [],
            'Industry Updates': []
        }

        text_body = sender._generate_text(digest_data, total=2)

        # Check content is present
        self.assertIn('AI DAILY DIGEST', text_body)
        self.assertIn('Processed 2 newsletters', text_body)
        self.assertIn('📄 PAPERS', text_body)
        self.assertIn('Research Paper Title', text_body)
        self.assertIn('This is a summary', text_body)
        self.assertIn('https://example.com/paper', text_body)
        self.assertIn('📰 NEWS', text_body)
        self.assertIn('Industry News', text_body)

    @patch('src.email_sender.build')
    @patch('src.email_sender.Credentials')
    def test_generate_html_digest(self, mock_creds, mock_build):
        """Test generating HTML digest."""
        sender = EmailSender('token', 'client_id', 'secret', 'from@example.com')

        digest_data = {
            'Papers': [
                {
                    'title': 'HTML Test Paper',
                    'summary': 'HTML summary content.',
                    'source': 'Source',
                    'link': 'https://example.com'
                }
            ],
            'News': [],
            'Tools': [],
            'Industry Updates': []
        }

        html_body = sender._generate_html(digest_data, total=1)

        # Check HTML structure
        self.assertIn('<html>', html_body)
        self.assertIn('</html>', html_body)
        self.assertIn('HTML Test Paper', html_body)
        self.assertIn('HTML summary content', html_body)
        self.assertIn('href="https://example.com"', html_body)

    @patch('src.email_sender.build')
    @patch('src.email_sender.Credentials')
    def test_send_digest_preview_mode(self, mock_creds, mock_build):
        """Test sending digest in preview mode (no actual send)."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        sender = EmailSender('token', 'client_id', 'secret', 'from@example.com')

        digest_data = {
            'Papers': [],
            'News': [],
            'Tools': [],
            'Industry Updates': []
        }

        # Should not raise exception
        sender.send_digest(
            to_email='recipient@example.com',
            digest_data=digest_data,
            total_newsletters=0,
            preview_only=True
        )

        # Verify no email was sent
        mock_service.users().messages().send.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
