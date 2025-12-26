"""Email sending functionality for the digest."""

import base64
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class EmailSender:
    """Send formatted digest emails using Gmail API."""

    # Category emoji mapping
    CATEGORY_ICONS = {
        "Papers": "📄",
        "News": "📰",
        "Tools": "🛠️",
        "Industry Updates": "📊"
    }

    def __init__(self, refresh_token: str, client_id: str, client_secret: str, from_email: str):
        """Initialize email sender.

        Args:
            refresh_token: OAuth 2.0 refresh token
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
            from_email: Email address to send from
        """
        self.from_email = from_email
        self.service = None
        self._authenticate(refresh_token, client_id, client_secret)

    def _authenticate(self, refresh_token: str, client_id: str, client_secret: str):
        """Authenticate with Gmail API."""
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )
            self.service = build('gmail', 'v1', credentials=creds)
        except Exception as e:
            raise RuntimeError(f"Failed to authenticate email sender: {e}")

    def send_digest(
        self,
        to_email: str,
        digest_data: Dict[str, List[Dict]],
        total_newsletters: int,
        preview_only: bool = False
    ):
        """Send or preview the digest email.

        Args:
            to_email: Recipient email address
            digest_data: Categorized and summarized digest data
            total_newsletters: Number of newsletters processed
            preview_only: If True, print to console instead of sending
        """
        # Generate email content
        subject = f"AI Daily Digest — {datetime.now().strftime('%B %d, %Y')}"
        html_body = self._generate_html(digest_data, total_newsletters)
        text_body = self._generate_text(digest_data, total_newsletters)

        if preview_only:
            self._print_preview(subject, text_body)
        else:
            self._send_email(to_email, subject, html_body, text_body)

    def _generate_html(self, digest_data: Dict[str, List[Dict]], total: int) -> str:
        """Generate HTML email body.

        Args:
            digest_data: Digest content
            total: Total newsletters processed

        Returns:
            HTML string
        """
        date_str = datetime.now().strftime('%B %d, %Y')

        html_parts = [
            '<html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">',
            '<div style="border-bottom: 3px solid #333; padding: 20px 0; margin-bottom: 30px;">',
            f'<h1 style="margin: 0; color: #333;">AI DAILY DIGEST</h1>',
            f'<p style="color: #666; margin: 10px 0 0 0;">{date_str} • Processed {total} newsletters</p>',
            '</div>'
        ]

        # Add categories
        for category, items in digest_data.items():
            if not items:
                continue

            icon = self.CATEGORY_ICONS.get(category, "•")
            html_parts.append(f'<h2 style="color: #2c5282; margin-top: 30px;">{icon} {category.upper()}</h2>')

            html_parts.append('<ol style="line-height: 1.8;">')
            for item in items:
                title = item.get('title', 'Untitled')
                summary = item.get('summary', '')
                source = item.get('source', 'Unknown')
                link = item.get('link', '')

                html_parts.append('<li style="margin-bottom: 20px;">')
                html_parts.append(f'<strong>{title}</strong><br>')
                html_parts.append(f'<span style="color: #444;">{summary}</span><br>')

                html_parts.append('<span style="color: #666; font-size: 0.9em;">')
                html_parts.append(f'Source: {source}')
                if link:
                    html_parts.append(f' | <a href="{link}" style="color: #2c5282;">Link</a>')
                html_parts.append('</span>')

                html_parts.append('</li>')
            html_parts.append('</ol>')

        # Footer
        html_parts.append('<div style="border-top: 2px solid #eee; margin-top: 40px; padding-top: 20px; color: #999; font-size: 0.9em;">')
        html_parts.append(f'<p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
        html_parts.append('</div>')

        html_parts.append('</body></html>')
        return ''.join(html_parts)

    def _generate_text(self, digest_data: Dict[str, List[Dict]], total: int) -> str:
        """Generate plain text email body.

        Args:
            digest_data: Digest content
            total: Total newsletters processed

        Returns:
            Plain text string
        """
        date_str = datetime.now().strftime('%B %d, %Y')

        lines = [
            "═" * 60,
            f"   AI DAILY DIGEST — {date_str}",
            f"   Processed {total} newsletters",
            "═" * 60,
            ""
        ]

        for category, items in digest_data.items():
            if not items:
                continue

            icon = self.CATEGORY_ICONS.get(category, "•")
            lines.append(f"\n{icon} {category.upper()}")
            lines.append("-" * 60)

            for i, item in enumerate(items, 1):
                title = item.get('title', 'Untitled')
                summary = item.get('summary', '')
                source = item.get('source', 'Unknown')
                link = item.get('link', '')

                lines.append(f"\n{i}. {title}")
                lines.append(f"   {summary}")
                lines.append(f"   Source: {source}" + (f" | {link}" if link else ""))

        lines.append("\n" + "═" * 60)
        return "\n".join(lines)

    def _print_preview(self, subject: str, body: str):
        """Print email preview to console.

        Args:
            subject: Email subject
            body: Email body (plain text)
        """
        logger.info("\n" + "=" * 70)
        logger.info("EMAIL PREVIEW")
        logger.info("=" * 70)
        logger.info(f"Subject: {subject}")
        logger.info("=" * 70)
        logger.info(body)
        logger.info("=" * 70 + "\n")

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str):
        """Send email via Gmail API.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML body
            text_body: Plain text body
        """
        try:
            # Create MIME message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.from_email
            message['To'] = to_email

            # Attach both plain text and HTML versions
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')

            message.attach(text_part)
            message.attach(html_part)

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Digest email sent to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise RuntimeError(f"Failed to send email: {e}")
