# Deployment Scripts

Modular deployment scripts for the AI Newsletter Digest.

## Prerequisites

Before running any deployment scripts, you need to set up the Google Cloud CLI (`gcloud`).

### 1. Install gcloud CLI

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**Linux or older versions of macOS:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
Download from: https://cloud.google.com/sdk/docs/install

### 2. Initialize and Authenticate

```bash
# Verify installation
gcloud version

# Initialize gcloud (interactive setup)
gcloud init

# Follow the prompts to:
# - Log in with your Google account
# - Select or create a project
# - Set default region (us-central1 recommended)

# Authenticate for application access
gcloud auth login

# Set application default credentials (for local testing)
gcloud auth application-default login
```

### 3. Verify Setup

```bash
# Check current configuration
gcloud config list

# Should show:
# - account: your-email@gmail.com
# - project: maia-proj3ct (or your project ID)
# - region: us-central1
```

### 5. Update config.yaml

Make sure `config.yaml` has your project settings:

```yaml
deployment:
  project_id: "your-project-id"  # From gcloud config list
  region: "us-central1"           # Your preferred region
```

## Scripts

### `oauth_setup.py`
**Purpose:** Interactive OAuth 2.0 setup for Gmail API access
**When to run:** Once, before first deployment. This is necessary to allow the Gmail API to act on behalf of the newsletter aggregator account. Needs to be executed once upon project setup.
**What it does:**
- Opens browser for Google OAuth consent
- Obtains refresh token for Gmail API
- Saves credentials to `.env` file

```bash
python scripts/oauth_setup.py
```

### `setup-secrets.sh`
**Purpose:** Create secrets in Google Secret Manager
**When to run:** Once, after OAuth setup
**What it does:**
- Reads credentials from `.env`
- Creates/updates secrets in Secret Manager
- Grants Cloud Run service account access

```bash
make setup-secrets
# or
./scripts/setup-secrets.sh
```

### `deploy.sh`
**Purpose:** Build and deploy application
**When to run:** Every time you update code
**What it does:**
- Builds Docker container
- Pushes to Google Container Registry
- Creates/updates Cloud Run Job
- Tests execution

```bash
make deploy
# or
./scripts/deploy.sh
```

### `setup-scheduler.sh`
**Purpose:** Configure Cloud Scheduler
**When to run:** Once, after first deployment
**What it does:**
- Reads schedule from `config.yaml`
- Creates/updates Cloud Scheduler job
- Configures daily trigger

```bash
make setup-scheduler
# or
./scripts/setup-scheduler.sh
```

### `common.sh`
**Purpose:** Shared functions and configuration
**When to run:** Never directly (sourced by other scripts)
**What it does:**
- Parses `config.yaml`
- Provides helper functions
- Sets common variables

## First-Time Deployment

```bash
# 1. Set up OAuth (interactive)
python scripts/oauth_setup.py

# 2. Create secrets
make setup-secrets

# 3. Deploy application
make deploy

# 4. Set up automatic schedule
make setup-scheduler
```

## Regular Updates

After making code changes:

```bash
make deploy
```

This will rebuild, redeploy, and test the updated application.

## Configuration

All scripts read from `config.yaml`:

```yaml
deployment:
  project_id: "your-project-id"
  region: "us-central1"

schedule:
  timezone: "America/New_York"
  hour: 7
  minute: 0
```

Change these values to deploy to a different project or adjust the schedule.

## Manual Commands

Manually trigger job:
```bash
~/google-cloud-sdk/bin/gcloud run jobs execute newsletter-digest --region us-central1
```

View scheduler:
```bash
~/google-cloud-sdk/bin/gcloud scheduler jobs describe newsletter-digest-trigger --location us-central1
```

## Troubleshooting

**"Secret already exists" errors:**
Normal! Scripts update existing secrets automatically.

**"Permission denied" errors:**
Make sure scripts are executable: `chmod +x scripts/*.sh`

**"Project not found" errors:**
Update `project_id` in `config.yaml`

**OAuth token expired:**
Re-run `python scripts/oauth_setup.py`
