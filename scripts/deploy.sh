#!/bin/bash
# Deploy application to Cloud Run Job
# Run this whenever you update code

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load common functions
source "$SCRIPT_DIR/common.sh"

echo "=== Deploying Newsletter Digest ==="
echo ""

# Configure gcloud
configure_gcloud

# Enable required APIs
echo ""
echo "→ Enabling required APIs..."
$GCLOUD services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  --quiet
echo "✓ APIs enabled"

# Build and push container
echo ""
echo "→ Building and pushing Docker container..."
cd "$PROJECT_ROOT"
$GCLOUD builds submit --tag $IMAGE_NAME --quiet

echo "✓ Container built and pushed"

# Get project number for secrets
PROJECT_NUMBER=$(get_project_number)

# Create or update Cloud Run Job
echo ""
echo "→ Deploying Cloud Run Job..."

if $GCLOUD run jobs describe $JOB_NAME --region $REGION >/dev/null 2>&1; then
  echo "  Updating existing job..."
  $GCLOUD run jobs update $JOB_NAME \
    --region $REGION \
    --image $IMAGE_NAME \
    --quiet
else
  echo "  Creating new job..."
  $GCLOUD run jobs create $JOB_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --memory 1Gi \
    --cpu 1 \
    --max-retries 2 \
    --task-timeout 15m \
    --set-secrets=GMAIL_REFRESH_TOKEN=gmail-refresh-token:latest,GMAIL_CLIENT_ID=gmail-client-id:latest,GMAIL_CLIENT_SECRET=gmail-client-secret:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,GMAIL_NEWSLETTER_ACCOUNT=gmail-newsletter-account:latest,GMAIL_DIGEST_RECIPIENT=gmail-digest-recipient:latest \
    --quiet
fi

echo "✓ Cloud Run Job deployed"

# Execute job to test
echo ""
echo "→ Testing job execution..."
$GCLOUD run jobs execute $JOB_NAME --region $REGION --wait

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "View logs:"
echo "  $GCLOUD logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit 50"
echo ""
echo "Manually trigger:"
echo "  $GCLOUD run jobs execute $JOB_NAME --region $REGION"
echo ""
echo "View in console:"
echo "  https://console.cloud.google.com/run/jobs/details/$REGION/$JOB_NAME?project=$PROJECT_ID"
