"""Configuration management for the newsletter digest application."""

import os
from pathlib import Path
from typing import List
import yaml
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from config.yaml and environment variables."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration.

        Args:
            config_path: Path to the YAML configuration file
        """
        # Load environment variables from .env file
        load_dotenv()

        # Load YAML configuration
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, 'r') as f:
            self._config = yaml.safe_load(f)

        # Validate required configuration
        self._validate()

    def _validate(self):
        """Validate that required configuration fields are present."""
        required_sections = ['schedule', 'newsletters', 'summarization']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate required environment variables
        required_env_vars = ['ANTHROPIC_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Schedule properties
    @property
    def timezone(self) -> str:
        return self._config['schedule']['timezone']

    @property
    def schedule_hour(self) -> int:
        return self._config['schedule']['hour']

    @property
    def schedule_minute(self) -> int:
        return self._config['schedule']['minute']

    # Gmail properties (from environment)
    @property
    def newsletter_account(self) -> str:
        """Get newsletter Gmail account from environment."""
        account = os.getenv('GMAIL_NEWSLETTER_ACCOUNT')
        if not account:
            raise ValueError("GMAIL_NEWSLETTER_ACCOUNT environment variable not set")
        return account

    @property
    def digest_recipient(self) -> str:
        """Get digest recipient email from environment."""
        recipient = os.getenv('GMAIL_DIGEST_RECIPIENT')
        if not recipient:
            raise ValueError("GMAIL_DIGEST_RECIPIENT environment variable not set")
        return recipient

    # Newsletter properties
    @property
    def allowed_senders(self) -> List[str]:
        return self._config['newsletters']['allowed_senders']

    # Summarization properties
    @property
    def model(self) -> str:
        return self._config['summarization']['model']

    @property
    def categories(self) -> List[str]:
        return self._config['summarization']['categories']

    @property
    def max_items_per_category(self) -> int:
        return self._config['summarization']['max_items_per_category']

    # Environment variable accessors
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return api_key

    @property
    def gmail_refresh_token(self) -> str:
        """Get Gmail OAuth refresh token from environment."""
        token = os.getenv('GMAIL_REFRESH_TOKEN')
        if not token:
            raise ValueError("GMAIL_REFRESH_TOKEN environment variable not set")
        return token

    @property
    def gmail_client_id(self) -> str:
        """Get Gmail OAuth client ID from environment."""
        client_id = os.getenv('GMAIL_CLIENT_ID')
        if not client_id:
            raise ValueError("GMAIL_CLIENT_ID environment variable not set")
        return client_id

    @property
    def gmail_client_secret(self) -> str:
        """Get Gmail OAuth client secret from environment."""
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        if not client_secret:
            raise ValueError("GMAIL_CLIENT_SECRET environment variable not set")
        return client_secret
