.PHONY: test build clean install help

help:
	@echo "AI Newsletter Digest - Build Commands"
	@echo "======================================"
	@echo "make install    - Install dependencies"
	@echo "make test       - Run unit and component tests"
	@echo "make build      - Run tests and build Docker image"
	@echo "make clean      - Clean build artifacts"

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
