.DEFAULT_GOAL := help

## Setup — install Python deps and compile Go binaries
setup:
	uv sync
	$(MAKE) build-go

## Dev — run Dagster dev server locally (host paths; see workspace.host.yaml)
dev:
	uv run dagster dev -h 0.0.0.0 -p 3000 -w workspace.host.yaml

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

## Build-go — compile Go scraper, fetcher, and trending binaries
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

## CI-check — run the same Python checks as GitHub Actions ci workflow
ci-check: lint
	uv run ruff format --check src/
	$(MAKE) typecheck
	uv run pytest tests/unit --cov-fail-under=80
	uv run pytest -m integration -k test_dagster_startup --no-cov

## CI-check-full — includes sqlfluff (requires DATABASE_URL + migrated DB)
ci-check-full: ci-check
	@test -n "$$DATABASE_URL" || (echo "DATABASE_URL required for sqlfluff" && exit 1)
	uv run sqlfluff lint dbt/

## Test-database — Postgres-backed FastAPI tier (DATABASE_URL required)
test-database:
	uv run pytest tests/integration/api --no-cov -v

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

.PHONY: setup dev test lint format typecheck build-go docker-up docker-down db-init dbt-build clean help doctor ci-check test-database
