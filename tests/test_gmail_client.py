"""Unit tests for GmailClient."""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gmail_client import GmailClient


class TestGmailClient(unittest.TestCase):
    """Test the GmailClient class."""

    @patch('src.gmail_client.build')
    @patch('src.gmail_client.Credentials')
    def test_authentication(self, mock_creds, mock_build):
        """Test Gmail API authentication."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GmailClient(
            refresh_token='test_refresh_token',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )

        self.assertIsNotNone(client.service)
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds.return_value)

    @patch('src.gmail_client.build')
    @patch('src.gmail_client.Credentials')
    def test_fetch_unread_emails(self, mock_creds, mock_build):
        """Test fetching unread emails."""
        # Mock the Gmail API service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock messages list response
        mock_service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'}
            ]
        }

        # Mock get message response
        def mock_get_message(userId, id, format):
            return MagicMock(execute=lambda: {
                'id': id,
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': f'Test Subject {id}'},
                        {'name': 'From', 'value': 'test@substack.com'},
                        {'name': 'Date', 'value': 'Thu, 26 Dec 2025 10:00:00'}
                    ],
                    'body': {'data': 'dGVzdCBjb250ZW50'},  # base64 "test content"
                    'parts': []
                }
            })

        mock_service.users().messages().get.side_effect = mock_get_message

        client = GmailClient('token', 'client_id', 'secret')
        emails = client.fetch_unread_emails(['@substack.com'], hours=24)

        self.assertIsInstance(emails, list)
        self.assertEqual(len(emails), 2)

    @patch('src.gmail_client.build')
    @patch('src.gmail_client.Credentials')
    def test_filter_by_allowed_senders(self, mock_creds, mock_build):
        """Test filtering emails by allowed senders."""
        client = GmailClient('token', 'client_id', 'secret')

        # Test allowed senders
        self.assertTrue(client._is_allowed_sender('test@substack.com', ['@substack.com']))
        self.assertTrue(client._is_allowed_sender('John <test@substack.com>', ['@substack.com']))
        self.assertFalse(client._is_allowed_sender('spam@example.com', ['@substack.com']))

    @patch('src.gmail_client.build')
    @patch('src.gmail_client.Credentials')
    def test_mark_as_read(self, mock_creds, mock_build):
        """Test marking emails as read."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GmailClient('token', 'client_id', 'secret')
        client.mark_as_read(['msg1', 'msg2'])

        # Verify batchModify was called
        mock_service.users().messages().batchModify.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
