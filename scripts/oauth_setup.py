#!/usr/bin/env python3
"""OAuth 2.0 setup script for Gmail API access.

This script guides you through the OAuth flow to obtain a refresh token
for accessing Gmail API. Run this once to generate credentials.
"""

import os
import json
import re
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Gmail API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Read, send, delete emails
    'https://www.googleapis.com/auth/gmail.send'      # Send emails
]


def update_env_file(refresh_token: str, client_id: str, client_secret: str):
    """Update .env file with OAuth credentials.

    Args:
        refresh_token: Gmail OAuth refresh token
        client_id: OAuth client ID
        client_secret: OAuth client secret
    """
    env_file = Path('.env')

    # Read existing .env or create from .env.example
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
    elif Path('.env.example').exists():
        with open('.env.example', 'r') as f:
            content = f.read()
    else:
        # Create minimal .env
        content = ""

    # Update or add each credential
    updates = {
        'GMAIL_REFRESH_TOKEN': refresh_token,
        'GMAIL_CLIENT_ID': client_id,
        'GMAIL_CLIENT_SECRET': client_secret
    }

    for key, value in updates.items():
        pattern = rf'^{key}=.*$'
        replacement = f'{key}={value}'

        if re.search(pattern, content, re.MULTILINE):
            # Replace existing value
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        else:
            # Add new line if not exists
            if content and not content.endswith('\n'):
                content += '\n'
            content += f'{replacement}\n'

    # Write back to .env
    with open('.env', 'w') as f:
        f.write(content)

    print(f"✓ Updated .env file with OAuth credentials")


def main():
    """Run OAuth flow and save credentials."""
    print("=" * 70)
    print("GMAIL API OAUTH SETUP")
    print("=" * 70)
    print()
    print("This script will help you obtain OAuth credentials for Gmail API.")
    print()
    print("PREREQUISITES:")
    print("1. Google Cloud project created")
    print("2. Gmail API enabled")
    print("3. OAuth 2.0 credentials downloaded as 'credentials.json'")
    print()
    print("=" * 70)
    print()

    # Check for credentials file
    creds_file = Path('credentials.json')
    if not creds_file.exists():
        print("ERROR: credentials.json not found!")
        print()
        print("Please download your OAuth 2.0 credentials from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop app)")
        print("3. Download the JSON file")
        print("4. Save it as 'credentials.json' in this directory")
        print()
        return 1

    print("✓ Found credentials.json")
    print()

    # Check if we already have a token
    token_file = Path('token.json')
    creds = None

    if token_file.exists():
        print("Found existing token.json - will refresh it")
        print()

    try:
        print("Starting OAuth flow...")
        print()
        print("A browser window will open for you to:")
        print("1. Sign in to the Gmail account (maiaproj3ct@gmail.com)")
        print("2. Grant access to the application")
        print()

        # Run OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )

        # This will open a browser for user authorization
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            success_message='Authorization successful! You can close this window.'
        )

        # Save credentials
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }

        with open('token.json', 'w') as f:
            json.dump(token_data, f, indent=2)

        print()
        print("✓ Credentials saved to: token.json")
        print()

        # Update .env file automatically
        print("→ Updating .env file...")
        update_env_file(
            refresh_token=creds.refresh_token,
            client_id=creds.client_id,
            client_secret=creds.client_secret
        )
        print()

        print("=" * 70)
        print("✓ SUCCESS! Setup complete.")
        print("=" * 70)
        print()
        print("Your .env file has been updated with OAuth credentials.")
        print()
        print("NEXT STEPS:")
        print("1. Test Gmail API access:")
        print("   python scripts/test_gmail.py")
        print()
        print("2. Run the application:")
        print("   python -m src --preview")
        print()
        print("=" * 70)
        print()
        print("IMPORTANT: Keep token.json and .env secure!")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("✗ ERROR")
        print("=" * 70)
        print(f"Failed to complete OAuth flow: {e}")
        print()
        print("Common issues:")
        print("- Make sure you're signed in to the correct Gmail account")
        print("- Check that the Gmail API is enabled in Google Cloud Console")
        print("- Verify OAuth consent screen is configured")
        print("- Ensure your email is added as a test user")
        print()
        return 1


if __name__ == '__main__':
    exit(main())
