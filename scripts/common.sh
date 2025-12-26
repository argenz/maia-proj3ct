#!/bin/bash
# Common functions and variables for deployment scripts

# Exit on error
set -e

# Use full path to gcloud if not in PATH
GCLOUD="${HOME}/google-cloud-sdk/bin/gcloud"

# Parse configuration from config.yaml
get_config() {
  local key=$1
  grep "$key:" config.yaml | sed "s/.*$key: *\"\(.*\)\".*/\1/" | sed "s/.*$key: *\([0-9]*\).*/\1/"
}

# Load deployment configuration
PROJECT_ID=$(get_config "project_id")
REGION=$(get_config "region")
TIMEZONE=$(get_config "timezone")
HOUR=$(get_config "hour")
MINUTE=$(get_config "minute")

# Validate required config
if [ -z "$PROJECT_ID" ] || [ -z "$REGION" ]; then
  echo "✗ ERROR: Missing deployment config in config.yaml"
  exit 1
fi

# Job configuration
JOB_NAME="newsletter-digest"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"

# Helper function: Check if .env file exists and has required variables
check_env_file() {
  if [ ! -f .env ]; then
    echo "✗ ERROR: .env file not found!"
    echo "Run: python scripts/oauth_setup.py"
    exit 1
  fi

  for var in GMAIL_REFRESH_TOKEN GMAIL_CLIENT_ID GMAIL_CLIENT_SECRET ANTHROPIC_API_KEY GMAIL_NEWSLETTER_ACCOUNT GMAIL_DIGEST_RECIPIENT; do
    if ! grep -q "^${var}=" .env; then
      echo "✗ ERROR: Missing $var in .env file!"
      exit 1
    fi
  done
}

# Helper function: Configure gcloud
configure_gcloud() {
  echo "→ Configuring gcloud..."
  $GCLOUD config set project $PROJECT_ID --quiet
  $GCLOUD config set run/region $REGION --quiet
  echo "✓ Project: $PROJECT_ID, Region: $REGION"
}

# Helper function: Get project number
get_project_number() {
  $GCLOUD projects describe $PROJECT_ID --format="value(projectNumber)"
}

# Helper function: Create or update secret
create_or_update_secret() {
  secret_name=$1
  secret_value=$2

  if echo -n "$secret_value" | $GCLOUD secrets create $secret_name --data-file=- 2>/dev/null; then
    echo "  ✓ Created secret: $secret_name"
  else
    echo -n "$secret_value" | $GCLOUD secrets versions add $secret_name --data-file=- >/dev/null
    echo "  ✓ Updated secret: $secret_name"
  fi
}
