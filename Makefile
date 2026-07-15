# =============================================================================
# FloodShield Makefile
# =============================================================================
# Usage: make <target>

.PHONY: help up down restart logs build test lint migrate seed clean

# ─────────────────────────────────────────────
# Default
# ─────────────────────────────────────────────
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─────────────────────────────────────────────
# Docker Compose
# ─────────────────────────────────────────────
up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

build: ## Build all images
	docker compose build

logs: ## Tail logs for all services
	docker compose logs -f

logs-api: ## Tail API logs only
	docker compose logs -f api

logs-db: ## Tail database logs only
	docker compose logs -f postgres

# ─────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────
test: ## Run tests
	docker compose exec api pytest -v

test-cov: ## Run tests with coverage
	docker compose exec api pytest --cov=app --cov-report=html -v

lint: ## Run linting
	docker compose exec api ruff check app/
	docker compose exec api ruff format --check app/

format: ## Format code
	docker compose exec api ruff format app/

shell: ## Open shell in API container
	docker compose exec api bash

db-shell: ## Open PostgreSQL shell
	docker compose exec postgres psql -U floodshield -d floodshield

# ─────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────
migrate: ## Run Alembic migrations
	docker compose exec api alembic upgrade head

migrate-new: ## Create new migration
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

migrate-down: ## Rollback last migration
	docker compose exec api alembic downgrade -1

seed: ## Load seed data
	docker compose exec api python -m app.seeds.load

# ─────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────
clean: ## Remove containers, volumes, and build cache
	docker compose down -v --remove-orphans
	docker system prune -f

clean-db: ## Remove postgres volume (destroys data)
	docker compose down -v
	@echo "Database volume removed."
