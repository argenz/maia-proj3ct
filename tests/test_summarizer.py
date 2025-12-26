"""Unit tests for Summarizer."""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.summarizer import Summarizer


class TestSummarizer(unittest.TestCase):
    """Test the Summarizer class."""

    @patch('src.summarizer.Anthropic')
    def test_summarize_success(self, mock_anthropic):
        """Test successful summarization."""
        # Mock Claude API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''{
            "Papers": [
                {
                    "title": "Test Paper",
                    "summary": "This is a test paper summary.",
                    "source": "Test Source",
                    "link": "https://example.com/paper"
                }
            ],
            "News": [
                {
                    "title": "Breaking News",
                    "summary": "Important news update.",
                    "source": "News Source",
                    "link": "https://example.com/news"
                }
            ],
            "Tools": [],
            "Industry Updates": []
        }'''
        mock_client.messages.create.return_value = mock_response

        summarizer = Summarizer(api_key='test_api_key', model='claude-sonnet-4-20250514')

        newsletter_items = [
            {
                'title': 'Test Newsletter',
                'content': 'This newsletter contains research papers and news.',
                'links': [{'url': 'https://example.com', 'text': 'Link'}],
                'source': 'Test Source'
            }
        ]

        result = summarizer.summarize(
            newsletter_items=newsletter_items,
            categories=['Papers', 'News', 'Tools', 'Industry Updates'],
            max_items_per_category=5
        )

        # Assertions
        self.assertIn('Papers', result)
        self.assertIn('News', result)
        self.assertEqual(len(result['Papers']), 1)
        self.assertEqual(len(result['News']), 1)
        self.assertEqual(result['Papers'][0]['title'], 'Test Paper')
        self.assertEqual(result['News'][0]['title'], 'Breaking News')

    @patch('src.summarizer.Anthropic')
    def test_summarize_with_malformed_json(self, mock_anthropic):
        """Test handling of malformed JSON response."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = 'This is not valid JSON'
        mock_client.messages.create.return_value = mock_response

        summarizer = Summarizer(api_key='test_api_key')

        newsletter_items = [{'title': 'Test', 'content': 'Content', 'links': [], 'source': 'Source'}]

        # Should raise RuntimeError for parse failure
        with self.assertRaises(RuntimeError):
            summarizer.summarize(
                newsletter_items=newsletter_items,
                categories=['Papers', 'News', 'Tools', 'Industry Updates'],
                max_items_per_category=5
            )

    @patch('src.summarizer.Anthropic')
    def test_format_newsletters(self, mock_anthropic):
        """Test formatting newsletters for Claude."""
        summarizer = Summarizer(api_key='test_api_key')

        newsletter_items = [
            {
                'title': 'Newsletter 1',
                'content': 'Content 1',
                'links': [{'url': 'https://example.com', 'text': 'Link 1'}],
                'source': 'Source 1'
            }
        ]

        formatted = summarizer._format_newsletters(newsletter_items)

        self.assertIn('Newsletter 1', formatted)
        self.assertIn('Content 1', formatted)
        self.assertIn('Source 1', formatted)
        self.assertIn('https://example.com', formatted)


if __name__ == '__main__':
    unittest.main(verbosity=2)
