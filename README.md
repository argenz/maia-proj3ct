# AI Newsletter Aggregator

A serverless system that aggregates AI newsletters from a dedicated Gmail inbox, summarizes content using Claude AI, and delivers a consolidated daily digest email.

## Overview

| | |
|---|---|
| **Problem** | Keeping up with multiple AI newsletters is time-consuming |
| **Solution** | Automated daily digest with AI-powered summarization |
| **Platform** | Google Cloud Run Jobs |
| **Cost** | ~$0/month (within free tier) |

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
newsletter-digest/
├── src/
│   ├── __main__.py          # Entry point
│   ├── gmail_client.py      # Gmail API integration
│   ├── content_extractor.py # Newsletter parsing
│   ├── summarizer.py        # Claude API summarization
│   ├── email_sender.py      # Digest email composition
│   └── config.py            # Configuration management
├── Dockerfile
├── requirements.txt
├── config.yaml              # Newsletter sources, schedule, preferences
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD pipeline
└── README.md
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
    - "@substack.com"
    - "newsletter@aiweekly.co"
    - "digest@therundown.ai"

summarization:
  model: "claude-sonnet-4-20250514"
  categories:
    - "Papers"
    - "News"
    - "Tools"
    - "Industry Updates"
  max_items_per_category: 5
```

## Setup

### Prerequisites

- Google Cloud account with billing enabled
- Gmail account for newsletters
- Anthropic API key
- Docker installed locally
- gcloud CLI installed

### 1. Google Cloud Setup

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  gmail.googleapis.com
```

### 2. Gmail OAuth Setup

```bash
# Run local OAuth flow (one-time)
python scripts/oauth_setup.py

# Store refresh token in Secret Manager
gcloud secrets create gmail-refresh-token \
  --data-file=token.json
```

### 3. Store Anthropic API Key

```bash
echo -n "your-api-key" | gcloud secrets create anthropic-api-key --data-file=-
```

### 4. Deploy

```bash
# Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/newsletter-digest

# Create Cloud Run Job
gcloud run jobs create newsletter-digest \
  --image gcr.io/YOUR_PROJECT_ID/newsletter-digest \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --max-retries 1 \
  --task-timeout 10m

# Create Cloud Scheduler trigger
gcloud scheduler jobs create http newsletter-digest-trigger \
  --location us-central1 \
  --schedule "0 7 * * *" \
  --time-zone "America/New_York" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/newsletter-digest:run" \
  --http-method POST \
  --oauth-service-account-email YOUR_PROJECT_ID@appspot.gserviceaccount.com
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m src

# Run with dry-run (no email sent)
python -m src --dry-run

# Preview digest in terminal
python -m src --preview
```

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
