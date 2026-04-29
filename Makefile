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
## Sources `.env` when present so DATABASE_URL matches compose/Postgres (see AGENTS.md).
db-init:
	bash -c 'set -a && [ -f .env ] && . ./.env; set +a; npx prisma db push'
	bash -c 'set -a && [ -f .env ] && . ./.env; set +a; ./node_modules/.bin/ts-node --compiler-options "{\"module\":\"CommonJS\"}" prisma/seed/seed.ts'

## DBT-build — install dbt deps and build all models
dbt-build:
	bash -c 'set -a && [ -f .env ] && . ./.env; set +a; cd dbt && dbt deps && dbt build'

## Doctor — verify uv and .env (Docker only needed for compose)
doctor:
	@command -v uv >/dev/null || (echo "Install uv: https://docs.astral.sh/uv/" && exit 1)
	@uv --version >/dev/null
	@test -f .env || (echo "Missing .env — copy from .env.example and fill values" && exit 1)
	@echo "doctor: ok (uv + .env). Use Docker when running docker compose."

## CI-check — run the same Python checks as GitHub Actions quality job
ci-check: lint
	uv run ruff format --check src/
	$(MAKE) typecheck
	uv run pytest -m unit --cov-fail-under=50
	uv run pytest -m api --no-cov
	uv run pytest -m integration -k test_dagster_startup --no-cov

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

.PHONY: setup dev test lint format typecheck build-go docker-up docker-down db-init dbt-build clean help doctor ci-check
