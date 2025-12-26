#!/bin/bash
# Setup script to configure GitHub Actions for CI/CD
# Run this once to create a service account for GitHub Actions

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load common functions
source "$SCRIPT_DIR/common.sh"

echo "=== Setting Up GitHub Actions for CI/CD ==="
echo ""

# Configure gcloud
configure_gcloud

echo ""
echo "→ Creating service account for GitHub Actions..."

SA_NAME="github-actions"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account
if gcloud iam service-accounts describe $SA_EMAIL >/dev/null 2>&1; then
  echo "  Service account already exists: $SA_EMAIL"
else
  gcloud iam service-accounts create $SA_NAME \
    --display-name="GitHub Actions CI/CD" \
    --description="Service account for GitHub Actions deployment"
  echo "  ✓ Created service account: $SA_EMAIL"
fi

echo ""
echo "→ Granting required permissions..."

# Grant required roles
for role in \
  roles/run.admin \
  roles/iam.serviceAccountUser \
  roles/storage.admin \
  roles/artifactregistry.writer
do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$role" \
    --quiet
done

echo "✓ Permissions granted"

echo ""
echo "→ Creating service account key..."

KEY_FILE="$PROJECT_ROOT/github-actions-key.json"

# Delete old key if exists
if [ -f "$KEY_FILE" ]; then
  rm "$KEY_FILE"
fi

# Create new key
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SA_EMAIL"

echo "✓ Key created: $KEY_FILE"

echo ""
echo "=== GitHub Actions Setup Complete! ==="
echo ""
echo "Next steps:"
echo ""
echo "1. Add GitHub Secret:"
echo "   a. Go to: https://github.com/YOUR_USERNAME/maia-proj3ct/settings/secrets/actions"
echo "   b. Click 'New repository secret'"
echo "   c. Name: GCP_SA_KEY"
echo "   d. Value: Copy entire contents of github-actions-key.json"
echo ""
echo "   Copy the key with:"
echo "   cat github-actions-key.json | pbcopy    # macOS"
echo "   cat github-actions-key.json             # Linux (then copy output)"
echo ""
echo "2. Delete the local key file (after copying to GitHub):"
echo "   rm github-actions-key.json"
echo ""
echo "3. Push to main branch to trigger deployment:"
echo "   git push origin main"
echo ""
echo "⚠️  IMPORTANT: Keep github-actions-key.json secure!"
echo "   Do NOT commit this file to git (it's in .gitignore)"
echo ""
