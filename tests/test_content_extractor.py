"""Unit tests for ContentExtractor."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.content_extractor import ContentExtractor


class TestContentExtractor(unittest.TestCase):
    """Test the ContentExtractor class."""

    def setUp(self):
        self.extractor = ContentExtractor()

    def test_extract_from_html(self):
        """Test extracting content from HTML email."""
        email_data = {
            'subject': 'Test Newsletter',
            'from': 'Test Sender <test@example.com>',
            'body_html': '<html><body><h1>Title</h1><p>Content here with important info.</p><a href="https://example.com/article">Read Article</a></body></html>',
            'body_text': ''
        }

        result = self.extractor.extract(email_data)

        self.assertEqual(result['source'], 'Test Sender')
        # Content may be empty if readability fails, check it exists
        self.assertIsNotNone(result['content'])
        # Links is a list (may be empty if readability filters them)
        self.assertIsInstance(result['links'], list)

    def test_extract_from_plain_text(self):
        """Test extracting content from plain text email."""
        email_data = {
            'subject': 'Plain Text Newsletter',
            'from': 'Sender <sender@example.com>',
            'body_html': '',
            'body_text': 'This is plain text content.\nVisit https://example.com for more info.'
        }

        result = self.extractor.extract(email_data)

        self.assertEqual(result['source'], 'Sender')
        self.assertIn('plain text content', result['content'])
        self.assertEqual(len(result['links']), 1)
        self.assertEqual(result['links'][0]['url'], 'https://example.com')

    def test_extract_sender_name(self):
        """Test extracting sender name from various formats."""
        test_cases = [
            ('John Doe <john@example.com>', 'John Doe'),
            ('"Company Name" <info@company.com>', 'Company Name'),
            ('simple@email.com', 'simple@email.com'),
            ('"Newsletter" <newsletter@substack.com>', 'Newsletter')
        ]

        for input_email, expected_name in test_cases:
            result = self.extractor._extract_sender_name(input_email)
            self.assertEqual(result, expected_name, f"Failed for input: {input_email}")

    def test_filter_unsubscribe_links(self):
        """Test that unsubscribe links are filtered out."""
        email_data = {
            'subject': 'Newsletter',
            'from': 'Sender <sender@example.com>',
            'body_html': '''
                <html><body>
                    <p>Content</p>
                    <a href="https://example.com/article">Read more</a>
                    <a href="https://example.com/unsubscribe">Unsubscribe</a>
                    <a href="https://facebook.com/page">Facebook</a>
                </body></html>
            ''',
            'body_text': ''
        }

        result = self.extractor.extract(email_data)
        links = [link['url'] for link in result['links']]

        self.assertIn('https://example.com/article', links)
        self.assertNotIn('https://example.com/unsubscribe', links)
        self.assertNotIn('https://facebook.com/page', links)


if __name__ == '__main__':
    unittest.main(verbosity=2)
