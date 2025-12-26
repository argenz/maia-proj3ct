"""Integration tests for the full workflow."""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.content_extractor import ContentExtractor
from src.summarizer import Summarizer
from src.email_sender import EmailSender


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    @patch('src.summarizer.Anthropic')
    @patch('src.email_sender.build')
    def test_extract_summarize_format_workflow(self, mock_build, mock_anthropic):
        """Test the complete extraction → summarization → formatting workflow."""
        # Mock Claude API
        mock_claude_client = MagicMock()
        mock_anthropic.return_value = mock_claude_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''{
            "Papers": [
                {
                    "title": "Integration Test Paper",
                    "summary": "Summary from Claude",
                    "source": "Test Source",
                    "link": "https://example.com"
                }
            ],
            "News": [],
            "Tools": [],
            "Industry Updates": []
        }'''
        mock_claude_client.messages.create.return_value = mock_response

        # Test email data
        email_data = {
            'subject': 'Weekly AI Newsletter',
            'from': 'AI Weekly <newsletter@aiweekly.co>',
            'body_html': '''
                <html>
                <body>
                    <h1>This Week in AI</h1>
                    <p>New research on transformer architectures shows promising results.</p>
                    <a href="https://example.com/paper">Read the paper</a>
                </body>
                </html>
            ''',
            'body_text': ''
        }

        # 1. Extract content
        extractor = ContentExtractor()
        extracted = extractor.extract(email_data)

        self.assertIsNotNone(extracted)
        self.assertEqual(extracted['source'], 'AI Weekly')
        self.assertIn('transformer', extracted['content'].lower())

        # 2. Summarize
        summarizer = Summarizer('test_api_key')
        digest = summarizer.summarize(
            newsletter_items=[extracted],
            categories=['Papers', 'News', 'Tools', 'Industry Updates'],
            max_items_per_category=5
        )

        self.assertIn('Papers', digest)
        self.assertEqual(len(digest['Papers']), 1)
        self.assertEqual(digest['Papers'][0]['title'], 'Integration Test Paper')

        # 3. Format as email
        sender = EmailSender('token', 'client_id', 'secret', 'from@example.com')
        text_body = sender._generate_text(digest, total=1)

        self.assertIn('AI DAILY DIGEST', text_body)
        self.assertIn('Integration Test Paper', text_body)
        self.assertIn('Summary from Claude', text_body)

    def test_multiple_newsletters_workflow(self):
        """Test processing multiple newsletters."""
        # Multiple test emails
        emails = [
            {
                'subject': 'Research Update',
                'from': 'Research <research@substack.com>',
                'body_html': '<html><body><p>Paper on scaling laws.</p></body></html>',
                'body_text': ''
            },
            {
                'subject': 'Tool Launch',
                'from': 'Tools <tools@newsletter.com>',
                'body_html': '<html><body><p>New AI tool released.</p></body></html>',
                'body_text': ''
            }
        ]

        # Extract all
        extractor = ContentExtractor()
        extracted_items = [extractor.extract(email) for email in emails]

        self.assertEqual(len(extracted_items), 2)
        self.assertEqual(extracted_items[0]['source'], 'Research')
        self.assertEqual(extracted_items[1]['source'], 'Tools')


if __name__ == '__main__':
    unittest.main(verbosity=2)
