.PHONY: help setup dev migrate test lint format typecheck pre-commit-install pre-commit docker-build docker-up docker-down docker-logs clean

help:
	@echo "LensAnalytics Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Development:"
	@echo "  make setup              Install dependencies with uv"
	@echo "  make dev                Start development server with hot reload"
	@echo "  make dev-all            Start all services (postgres + api) with docker-compose"
	@echo ""
	@echo "Database:"
	@echo "  make migrate            Run pending Alembic migrations"
	@echo "  make migrate-down       Rollback one migration"
	@echo "  make migrate-history    Show migration history"
	@echo "  make migrate-new        Create new migration (use MESSAGE='description')"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint               Run ruff linter"
	@echo "  make format             Format code with black and ruff"
	@echo "  make typecheck          Run mypy static analysis"
	@echo "  make pre-commit-install Install git hooks (pre-commit)"
	@echo "  make pre-commit         Run pre-commit on all files"
	@echo "  make test               Run pytest suite"
	@echo "  make test-cov           Run tests with coverage"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build       Build Docker images"
	@echo "  make docker-up          Start containers (docker compose up)"
	@echo "  make docker-down        Stop containers"
	@echo "  make docker-logs        View container logs"
	@echo "  make docker-clean       Remove containers and volumes"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean              Remove cache files and build artifacts"
	@echo "  make health             Check API health endpoint"

# Setup & Development
setup:
	@echo "Installing dependencies with uv..."
	uv sync --extra dev

dev:
	@echo "Starting FastAPI development server..."
	uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev-all:
	@echo "Starting all services with docker-compose..."
	docker compose up --build

# Database Migrations
migrate:
	@echo "Running pending Alembic migrations..."
	uv run alembic upgrade head

migrate-down:
	@echo "Rolling back one migration..."
	uv run alembic downgrade -1

migrate-history:
	@echo "Showing migration history..."
	uv run alembic history

migrate-new:
	@ifndef MESSAGE
		@echo "Error: MESSAGE variable not set"
		@echo "Usage: make migrate-new MESSAGE='Add new column'"
		@exit 1
	endif
	@echo "Creating new migration: $(MESSAGE)"
	uv run alembic revision --autogenerate -m "$(MESSAGE)"

# Code Quality
lint:
	@echo "Running ruff..."
	uv run ruff check .

format:
	@echo "Formatting code with black..."
	uv run black .
	@echo "Auto-fixing lint with ruff..."
	uv run ruff check . --fix

typecheck:
	@echo "Running mypy..."
	uv run mypy backend

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

pre-commit:
	@echo "Running pre-commit on all files..."
	uv run pre-commit run --all-files

test:
	@echo "Running pytest..."
	uv run pytest -v

test-cov:
	@echo "Running pytest with coverage..."
	uv run pytest --cov=backend --cov-report=html --cov-report=term

# Docker
docker-build:
	@echo "Building Docker images..."
	docker compose build

docker-up:
	@echo "Starting containers..."
	docker compose up -d

docker-down:
	@echo "Stopping containers..."
	docker compose down

docker-logs:
	@echo "Tailing logs..."
	docker compose logs -f

docker-clean:
	@echo "Removing containers and volumes..."
	docker compose down -v

# Utilities
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned!"

health:
	@echo "Checking API health..."
	curl -s http://localhost:8000/health | python -m json.tool || echo "API not responding"
