"""Gmail API client for fetching and managing newsletter emails."""

import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailClient:
    """Client for interacting with Gmail API to fetch and manage emails."""

    def __init__(self, refresh_token: str, client_id: str, client_secret: str):
        """Initialize Gmail client with OAuth credentials.

        Args:
            refresh_token: OAuth 2.0 refresh token
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
        """
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using refresh token."""
        try:
            # Create credentials from refresh token
            creds = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=creds)
            print("✓ Gmail API authentication successful")

        except Exception as e:
            raise RuntimeError(f"Failed to authenticate with Gmail API: {e}")

    def fetch_unread_emails(
        self,
        allowed_senders: List[str],
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Fetch unread emails from the last N hours filtered by allowed senders.

        Args:
            allowed_senders: List of allowed sender domains/emails (e.g., "@substack.com")
            hours: Number of hours to look back (default: 24)

        Returns:
            List of email dictionaries containing metadata and content
        """
        try:
            # Calculate date filter (emails after this timestamp)
            after_date = datetime.now() - timedelta(hours=hours)
            after_timestamp = int(after_date.timestamp())

            # Build query: unread emails from last N hours
            query = f"is:unread after:{after_timestamp}"

            print(f"Fetching unread emails from last {hours} hours...")

            # List messages matching query
            results = self.service.users().messages().list(
                userId='me',
                q=query
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                print("No unread emails found")
                return []

            print(f"Found {len(messages)} unread emails, filtering by allowed senders...")

            # Fetch full details for each message
            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'])

                # Check if sender is in allowed list
                if email_data and self._is_allowed_sender(email_data['from'], allowed_senders):
                    emails.append(email_data)

            print(f"✓ Filtered to {len(emails)} newsletter emails")
            return emails

        except HttpError as e:
            if e.resp.status == 401:
                raise RuntimeError("Gmail API authentication failed. Token may be expired.")
            raise RuntimeError(f"Gmail API error: {e}")

    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full details for a specific email.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email details or None if failed
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']

            # Extract headers
            subject = self._get_header(headers, 'Subject')
            from_email = self._get_header(headers, 'From')
            date = self._get_header(headers, 'Date')

            # Extract body content
            body_html = self._get_body(message['payload'], 'text/html')
            body_text = self._get_body(message['payload'], 'text/plain')

            return {
                'id': message_id,
                'subject': subject,
                'from': from_email,
                'date': date,
                'body_html': body_html,
                'body_text': body_text
            }

        except Exception as e:
            print(f"Warning: Failed to fetch email {message_id}: {e}")
            return None

    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Extract a specific header value from email headers."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""

    def _get_body(self, payload: Dict, mime_type: str) -> str:
        """Extract email body content for a specific MIME type."""
        # Check if payload has the requested MIME type
        if payload.get('mimeType') == mime_type:
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')

        # Check parts recursively
        parts = payload.get('parts', [])
        for part in parts:
            if part.get('mimeType') == mime_type:
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')

            # Recursive check for nested parts
            if 'parts' in part:
                result = self._get_body(part, mime_type)
                if result:
                    return result

        return ""

    def _is_allowed_sender(self, from_email: str, allowed_senders: List[str]) -> bool:
        """Check if email sender is in allowed list.

        Args:
            from_email: Email sender string (e.g., "Name <email@domain.com>")
            allowed_senders: List of allowed patterns (domains or full emails)

        Returns:
            True if sender is allowed
        """
        from_email_lower = from_email.lower()

        for allowed in allowed_senders:
            if allowed.lower() in from_email_lower:
                return True

        return False

    def mark_as_read(self, message_ids: List[str]):
        """Mark emails as read.

        Args:
            message_ids: List of Gmail message IDs to mark as read
        """
        if not message_ids:
            return

        try:
            # Batch modify to mark as read
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()

            print(f"✓ Marked {len(message_ids)} emails as read")

        except HttpError as e:
            print(f"Warning: Failed to mark emails as read: {e}")
