# AI Newsletter Aggregator

A serverless system that aggregates AI newsletters from a dedicated Gmail inbox, summarizes content using Claude AI, and delivers a consolidated daily digest email.

## Overview

| | |
|---|---|
| **Problem** | Keeping up with multiple AI newsletters is time-consuming |
| **Solution** | Automated daily digest with AI-powered summarization |
| **Platform** | Google Cloud Run Jobs |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Google Cloud                             │
│                                                                 │
│   ┌──────────────┐         ┌─────────────────────────────────┐  │
│   │   Cloud      │ triggers│       Cloud Run Job             │  │
│   │  Scheduler   │────────▶│   (newsletter-digest)           │  │
│   │  (daily)     │         │                                 │  │
│   └──────────────┘         │  1. Fetch emails (Gmail API)    │  │
│                            │  2. Parse newsletter content    │  │
│                            │  3. Summarize (Claude API)      │  │
│                            │  4. Send digest email           │  │
│                            └────────────┬────────────────────┘  │
│                                         │                       │
│         ┌───────────────────────────────┼───────────────────┐   │
│         ▼                               ▼                   ▼   │
│  ┌─────────────┐              ┌──────────────┐    ┌───────────┐ │
│  │   Secret    │              │    Cloud     │    │  Cloud    │ │
│  │   Manager   │              │   Storage    │    │  Logging  │ │
│  │             │              │   (state)    │    │           │ │
│  │ • Gmail     │              │ • Processed  │    │ • Errors  │ │
│  │   OAuth     │              │   email IDs  │    │ • Metrics │ │
│  │ • Anthropic │              │              │    │           │ │
│  │   API key   │              │              │    │           │ │
│  └─────────────┘              └──────────────┘    └───────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Purpose |
|-----------|---------|
| **Cloud Run Job** | Containerized Python app that executes the full workflow |
| **Cloud Scheduler** | Triggers the job daily at configured time (e.g., 7:00 AM) |
| **Secret Manager** | Securely stores Gmail OAuth refresh token and Anthropic API key |
| **Cloud Storage** | Tracks processed email IDs to prevent duplicates (optional) |
| **Cloud Logging** | Automatic log capture, error tracking, and alerting |

## Daily Workflow

1. **Trigger** — Cloud Scheduler invokes Cloud Run Job
2. **Authenticate** — Retrieve OAuth token from Secret Manager, refresh access token
3. **Fetch** — Get unread emails from last 24 hours via Gmail API
4. **Parse** — Extract content from HTML/plain text newsletters
5. **Summarize** — Send to Claude API for categorization and summarization
6. **Deliver** — Compose and send digest email to primary inbox
7. **Cleanup** — Mark emails as processed, log completion status

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.11+ |
| Container | Docker |
| Email | Gmail API (OAuth 2.0) |
| AI | Anthropic Claude API |
| Parsing | BeautifulSoup, readability-lxml |
| Infrastructure | Google Cloud (Cloud Run, Scheduler, Secret Manager) |

## Project Structure

```
maia-proj3ct/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── config.py            # Configuration management
│   ├── gmail_client.py      # Gmail API integration
│   ├── content_extractor.py # Newsletter parsing
│   ├── summarizer.py        # Claude API summarization
│   └── email_sender.py      # Digest email composition
├── tests/
├── scripts/                 # Setup and Deployment Scripts
├── .github/
│   └── workflows/
│       ├── ci.yml           # Continuous Integration
│       └── deploy.yml       # Continuous Deployment
├── .env.example             # Template for environment variables
├── Dockerfile
├── Makefile                 # Deployment commands (make deploy, make setup-secrets, etc.)
├── README.md
├── config.yaml              # Newsletter sources, schedule, preferences
└── requirements.txt         # Python dependencies

# Generated during setup (not in git):
├── .env                     # Environment variables (OAuth tokens, API keys)
├── credentials.json         # Gmail OAuth credentials
└── token.json               # Gmail OAuth refresh token
```

## Configuration

```yaml
# config.yaml
schedule:
  timezone: "America/New_York"
  hour: 7
  minute: 0

gmail:
  newsletter_account: "ai-newsletters@gmail.com"
  digest_recipient: "your-main@gmail.com"
  
newsletters:
  allowed_senders:
    - "@..."

summarization:
  model: "claude-sonnet-4-20250514"
  categories:
    - "Papers"
    - "News"
    - "Tools"
    - "Industry Updates"
  max_items_per_category: 5
```

## Prerequisites

- Google Cloud account with billing enabled
- New Gmail account for receiving newsletters
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Docker installed locally
- gcloud CLI ([installation guide](https://cloud.google.com/sdk/docs/install))

### gcloud Setup

```bash
# Install gcloud CLI
brew install --cask google-cloud-sdk  # macOS
# For Linux/Windows: see https://cloud.google.com/sdk/docs/install

# Initialize and authenticate
gcloud init
gcloud auth login
gcloud auth application-default login

# Set your project and enable required APIs
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com gmail.googleapis.com
```

## Quick Start

**Automated deployment** (recommended):

```bash
# 1. Set up Gmail OAuth (opens browser)
python scripts/oauth_setup.py

# 2. Store secrets in Secret Manager
make setup-secrets

# 3. Deploy to Cloud Run
make deploy

# 4. Configure daily schedule
make setup-scheduler
```

**Update after code changes:**
```bash
make deploy
```

## Deployment

### Automated Scripts (Recommended)

The `scripts/` directory contains automated deployment tools:

| Script | Purpose | When to Run |
|--------|---------|-------------|
| `oauth_setup.py` | Gmail OAuth setup | Once (initial setup) |
| `setup-secrets.sh` | Create secrets in Secret Manager | Once (initial setup) |
| `deploy.sh` | Build & deploy to Cloud Run | Every code update |
| `setup-scheduler.sh` | Configure Cloud Scheduler | Once (initial setup) |
| `setup-github-actions.sh` | GitHub Actions service account | Once (if using CI/CD) |

### Manual Deployment (Alternative)

If you prefer manual control:

```bash
# Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/newsletter-digest

# Create Cloud Run Job
gcloud run jobs create newsletter-digest \
  --image gcr.io/YOUR_PROJECT_ID/newsletter-digest \
  --region us-central1 \
  --memory 512Mi --cpu 1 --max-retries 1 --task-timeout 10m

# Create Cloud Scheduler trigger (daily 7 AM)
gcloud scheduler jobs create http newsletter-digest-trigger \
  --location us-central1 \
  --schedule "0 7 * * *" \
  --time-zone "America/New_York" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/newsletter-digest:run" \
  --http-method POST \
  --oauth-service-account-email YOUR_PROJECT_ID@appspot.gserviceaccount.com
```

### Manual Commands

```bash
# Trigger job manually
gcloud run jobs execute newsletter-digest --region us-central1

# View scheduler status
gcloud scheduler jobs describe newsletter-digest-trigger --location us-central1

# View logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=newsletter-digest" --limit 50
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Secret already exists" | Normal - scripts update existing secrets |
| "Permission denied" | Run `chmod +x scripts/*.sh` |
| "Project not found" | Update `project_id` in `config.yaml` |
| OAuth token expired | Re-run `python scripts/oauth_setup.py` |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m src

# Dry-run (no email sent)
python -m src --dry-run

# Preview digest in terminal
python -m src --preview
```

## CI/CD with GitHub Actions

Automated workflows in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to non-main branches, PRs | Run tests and build validation |
| `deploy.yml` | Push to `main` | Auto-deploy to Cloud Run |

### Setup

```bash
# 1. Complete initial deployment
make setup-secrets && make deploy && make setup-scheduler

# 2. Create GitHub Actions service account
make setup-github-actions

# 3. Add GCP_SA_KEY secret to GitHub
# Copy: cat github-actions-key.json
# Go to: Settings → Secrets → Actions → New secret
# Name: GCP_SA_KEY
# Value: Paste JSON key
# Then: rm github-actions-key.json
```

### Usage

Push to `main` branch to trigger automatic deployment:
```bash
git push origin main
```

Check workflow status at: `https://github.com/YOUR_USERNAME/maia-proj3ct/actions`

**Note:** Auto-deployment only updates the Cloud Run Job image. The job still runs on its scheduled time (to save API credits).

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid credentials" | Re-run `make setup-github-actions` and update `GCP_SA_KEY` secret |
| "Permission denied" | Re-run `make setup-github-actions` |
| Job execution fails | Verify secrets: `gcloud secrets list` |

## Cost Estimate

| Service | Monthly Usage | Cost |
|---------|---------------|------|
| Cloud Run Jobs | 30 runs × 10 min | $0.00 (free tier) |
| Cloud Scheduler | 1 job | $0.00 (3 free jobs) |
| Secret Manager | 3 secrets, 30 accesses | $0.00 (free tier) |
| Cloud Storage | < 1 MB state file | $0.00 (free tier) |
| **Total** | | **$0.00** |

## Digest Output Example

```
═══════════════════════════════════════════════════════
   AI DAILY DIGEST — December 26, 2025
   Processed 8 newsletters
═══════════════════════════════════════════════════════

📄 TOP PAPERS
1. [Paper Title] - Brief summary...
   Source: Newsletter Name | Link

2. [Paper Title] - Brief summary...
   Source: Newsletter Name | Link

📰 NEWS
1. [Headline] - Summary...
   Source: Newsletter Name | Link

🛠️ TOOLS & LAUNCHES
1. [Tool Name] - Description...
   Source: Newsletter Name | Link

📊 INDUSTRY UPDATES
1. [Update] - Summary...
   Source: Newsletter Name | Link

═══════════════════════════════════════════════════════
```

## License

MIT
