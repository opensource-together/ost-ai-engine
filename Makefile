.DEFAULT_GOAL := help

## Setup — install Python deps and compile Go binaries
setup:
	uv sync
	$(MAKE) build-go

## Dev — run Dagster dev server locally
dev:
	uv run dagster dev -h 0.0.0.0 -p 3000

## Test — run pytest with coverage
test:
	uv run pytest

## Lint — check code with ruff
lint:
	uv run ruff check src/

## Format — auto-format code with ruff
format:
	uv run ruff format src/

## Typecheck — run mypy strict type checking
typecheck:
	uv run mypy src/

## Build-go — compile Go scraper and fetcher binaries
build-go:
	bash scripts/go_binary_gen.sh

## Docker-up — start all services
docker-up:
	docker compose up --build -d

## Docker-down — stop all services
docker-down:
	docker compose down

## DB-init — apply Prisma schema and seed data
db-init:
	npx prisma db push
	npx ts-node prisma/seed/seed.ts

## DBT-build — install dbt deps and build all models
dbt-build:
	cd dbt && dbt deps && dbt build

## Clean — remove Dagster storage and Python caches
clean:
	bash scripts/clean_dagster.sh
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache .mypy_cache htmlcov .coverage

## Help — show available targets
help:
	@echo "Available targets:"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'

.PHONY: setup dev test lint format typecheck build-go docker-up docker-down db-init dbt-build clean help
