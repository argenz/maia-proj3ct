#!/bin/bash
# One-time setup: Configure Cloud Scheduler to run job daily
# Run this once after deploying the application

# Get directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load common functions
source "$SCRIPT_DIR/common.sh"

echo "=== Setting Up Cloud Scheduler ==="
echo ""

# Configure gcloud
configure_gcloud

# Enable Cloud Scheduler API
echo ""
echo "→ Enabling Cloud Scheduler API..."
$GCLOUD services enable cloudscheduler.googleapis.com --quiet
echo "✓ API enabled"

# Build cron schedule from config.yaml
CRON_SCHEDULE="$MINUTE $HOUR * * *"

echo ""
echo "→ Configuring Cloud Scheduler..."
echo "  Schedule: $CRON_SCHEDULE ($TIMEZONE)"
echo "  Time: ${HOUR}:$(printf "%02d" $MINUTE) $TIMEZONE"

# Get project number for service account
PROJECT_NUMBER=$(get_project_number)

# Create or update scheduler job
SCHEDULER_NAME="${JOB_NAME}-trigger"

if $GCLOUD scheduler jobs describe $SCHEDULER_NAME --location $REGION >/dev/null 2>&1; then
  echo ""
  echo "  Updating existing scheduler..."
  $GCLOUD scheduler jobs update http $SCHEDULER_NAME \
    --location $REGION \
    --schedule "$CRON_SCHEDULE" \
    --time-zone "$TIMEZONE" \
    --quiet
else
  echo ""
  echo "  Creating new scheduler..."
  $GCLOUD scheduler jobs create http $SCHEDULER_NAME \
    --location $REGION \
    --schedule "$CRON_SCHEDULE" \
    --time-zone "$TIMEZONE" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method POST \
    --oauth-service-account-email ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
    --quiet
fi

echo "✓ Cloud Scheduler configured"

echo ""
echo "=== Scheduler Setup Complete! ==="
echo ""
echo "The job will run automatically:"
echo "  Schedule: Daily at ${HOUR}:$(printf "%02d" $MINUTE) $TIMEZONE"
echo ""
echo "View scheduler:"
echo "  $GCLOUD scheduler jobs describe $SCHEDULER_NAME --location $REGION"
echo ""
echo "Manually trigger scheduler:"
echo "  $GCLOUD scheduler jobs run $SCHEDULER_NAME --location $REGION"
echo ""
echo "View in console:"
echo "  https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
