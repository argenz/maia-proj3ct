"""Content extraction from newsletter emails."""

import re
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from readability import Document

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract and clean content from newsletter HTML/text."""

    def extract(self, email_data: Dict) -> Dict:
        """Extract structured content from an email.

        Args:
            email_data: Dictionary containing email metadata and body

        Returns:
            Dictionary with extracted content: title, content, links, source
        """
        # Prefer HTML content if available, fall back to plain text
        html_content = email_data.get('body_html', '')
        text_content = email_data.get('body_text', '')

        if html_content:
            return self._extract_from_html(html_content, email_data)
        elif text_content:
            return self._extract_from_text(text_content, email_data)
        else:
            return {
                'title': email_data.get('subject', 'Untitled'),
                'content': '',
                'links': [],
                'source': email_data.get('from', 'Unknown')
            }

    def _extract_from_html(self, html: str, email_data: Dict) -> Dict:
        """Extract content from HTML email.

        Args:
            html: Raw HTML content
            email_data: Email metadata

        Returns:
            Extracted content dictionary
        """
        try:
            # Use readability to extract main content
            doc = Document(html)
            title = doc.title()
            summary_html = doc.summary()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(summary_html, 'lxml')

            # Extract text content
            text = soup.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)

            # Extract links
            links = self._extract_links(soup)

            return {
                'title': title or email_data.get('subject', 'Untitled'),
                'content': text,
                'links': links,
                'source': self._extract_sender_name(email_data.get('from', 'Unknown'))
            }

        except Exception as e:
            logger.warning(f"Failed to extract HTML content: {e}")
            # Fallback to basic extraction
            return self._basic_html_extract(html, email_data)

    def _extract_from_text(self, text: str, email_data: Dict) -> Dict:
        """Extract content from plain text email.

        Args:
            text: Plain text content
            email_data: Email metadata

        Returns:
            Extracted content dictionary
        """
        # Clean up text
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Extract URLs from text
        url_pattern = r'https?://[^\s<>"{}\\|^`\[\]]+'
        links = [{'url': url, 'text': url} for url in re.findall(url_pattern, text)]

        return {
            'title': email_data.get('subject', 'Untitled'),
            'content': text,
            'links': links,
            'source': self._extract_sender_name(email_data.get('from', 'Unknown'))
        }

    def _basic_html_extract(self, html: str, email_data: Dict) -> Dict:
        """Fallback: Basic HTML extraction without readability.

        Args:
            html: Raw HTML content
            email_data: Email metadata

        Returns:
            Extracted content dictionary
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style elements
        for element in soup(['script', 'style', 'head']):
            element.decompose()

        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # Extract links
        links = self._extract_links(soup)

        return {
            'title': email_data.get('subject', 'Untitled'),
            'content': text,
            'links': links,
            'source': self._extract_sender_name(email_data.get('from', 'Unknown'))
        }

    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links from parsed HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of dictionaries with 'url' and 'text' keys
        """
        links = []
        for a_tag in soup.find_all('a', href=True):
            url = a_tag['href']
            text = a_tag.get_text(strip=True)

            # Filter out common newsletter footer links
            if self._is_content_link(url, text):
                links.append({
                    'url': url,
                    'text': text or url
                })

        return links

    def _is_content_link(self, url: str, text: str) -> bool:
        """Determine if a link is actual content (not unsubscribe, footer, etc).

        Args:
            url: Link URL
            text: Link text

        Returns:
            True if link appears to be content
        """
        # Filter out common non-content links
        filter_keywords = [
            'unsubscribe',
            'manage preferences',
            'update profile',
            'view in browser',
            'privacy policy',
            'terms of service',
            'contact us',
            'twitter.com',
            'facebook.com',
            'linkedin.com',
            'instagram.com'
        ]

        url_lower = url.lower()
        text_lower = text.lower()

        for keyword in filter_keywords:
            if keyword in url_lower or keyword in text_lower:
                return False

        # Must be a valid HTTP(S) URL
        if not url.startswith(('http://', 'https://')):
            return False

        return True

    def _extract_sender_name(self, from_email: str) -> str:
        """Extract readable sender name from email address.

        Args:
            from_email: Email "From" field (e.g., "Name <email@domain.com>")

        Returns:
            Cleaned sender name
        """
        # Pattern: "Name <email@domain.com>" -> "Name"
        match = re.match(r'^(.+?)\s*<', from_email)
        if match:
            name = match.group(1).strip()
            # Remove quotes if present
            name = name.strip('"\'')
            return name

        # Fallback: use email address
        email_match = re.search(r'<(.+?)>', from_email)
        if email_match:
            return email_match.group(1)

        return from_email
