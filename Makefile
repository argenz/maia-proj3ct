.PHONY: test build clean install setup-secrets setup-scheduler deploy help

help:
	@echo "AI Newsletter Digest - Commands"
	@echo "================================="
	@echo ""
	@echo "Local Development:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run unit and component tests"
	@echo "  make build            - Build Docker image locally"
	@echo "  make clean            - Clean build artifacts"
	@echo ""
	@echo "Cloud Deployment:"
	@echo "  make setup-secrets    - One-time: Create secrets in Secret Manager"
	@echo "  make deploy           - Deploy application to Cloud Run"
	@echo "  make setup-scheduler  - One-time: Configure Cloud Scheduler"
	@echo ""
	@echo "First-time deployment:"
	@echo "  1. make setup-secrets"
	@echo "  2. make deploy"
	@echo "  3. make setup-scheduler"
	@echo ""
	@echo "Regular updates:"
	@echo "  make deploy"

install:
	pip install -r requirements.txt

test:
	@echo "Running unit and component tests..."
	python -m src --test

build: test
	@echo "Building Docker image..."
	docker build -t newsletter-digest:latest .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Cloud deployment commands

setup-secrets:
	@./scripts/setup-secrets.sh

deploy:
	@./scripts/deploy.sh

setup-scheduler:
	@./scripts/setup-scheduler.sh
