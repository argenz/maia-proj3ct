#!/bin/bash
# One-time setup: Create secrets in Google Secret Manager
# Run this once after OAuth setup is complete

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load common functions
source "$SCRIPT_DIR/common.sh"

echo "=== Setting Up Secrets ==="
echo ""

# Check prerequisites
check_env_file
configure_gcloud

# Enable required APIs
echo ""
echo "→ Enabling Secret Manager API..."
$GCLOUD services enable secretmanager.googleapis.com --quiet
echo "✓ API enabled"

# Load credentials from .env
echo ""
echo "→ Loading credentials from .env..."
cd "$PROJECT_ROOT"

export GMAIL_REFRESH_TOKEN=$(grep GMAIL_REFRESH_TOKEN .env | cut -d '=' -f2)
export GMAIL_CLIENT_ID=$(grep GMAIL_CLIENT_ID .env | cut -d '=' -f2)
export GMAIL_CLIENT_SECRET=$(grep GMAIL_CLIENT_SECRET .env | cut -d '=' -f2)
export ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY .env | cut -d '=' -f2)
export GMAIL_NEWSLETTER_ACCOUNT=$(grep GMAIL_NEWSLETTER_ACCOUNT .env | cut -d '=' -f2)
export GMAIL_DIGEST_RECIPIENT=$(grep GMAIL_DIGEST_RECIPIENT .env | cut -d '=' -f2)

echo "✓ Credentials loaded"

# Create or update secrets
echo ""
echo "→ Creating/updating secrets in Secret Manager..."

create_or_update_secret "gmail-refresh-token" "$GMAIL_REFRESH_TOKEN"
create_or_update_secret "gmail-client-id" "$GMAIL_CLIENT_ID"
create_or_update_secret "gmail-client-secret" "$GMAIL_CLIENT_SECRET"
create_or_update_secret "anthropic-api-key" "$ANTHROPIC_API_KEY"
create_or_update_secret "gmail-newsletter-account" "$GMAIL_NEWSLETTER_ACCOUNT"
create_or_update_secret "gmail-digest-recipient" "$GMAIL_DIGEST_RECIPIENT"

# Grant access to compute service account
echo ""
echo "→ Granting service account access to secrets..."
PROJECT_NUMBER=$(get_project_number)

for secret in gmail-refresh-token gmail-client-id gmail-client-secret anthropic-api-key gmail-newsletter-account gmail-digest-recipient; do
  $GCLOUD secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet 2>/dev/null || true
done
echo "✓ Permissions granted"

echo ""
echo "=== Secrets Setup Complete! ==="
echo ""
echo "Next steps:"
echo "  1. Deploy the application: ./scripts/deploy.sh"
echo "  2. Set up scheduler: ./scripts/setup-scheduler.sh"
