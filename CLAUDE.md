# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OST Linker is the AI-powered recommendation engine for [OpenSourceTogether](https://opensource-together.com/). It scrapes GitHub for open-source projects, classifies them via LLM, computes embeddings, and surfaces personalized recommendations to users via cosine similarity (pgvector).

## Common Commands

### Development Setup
```bash
cp .env.example .env                      # Configure environment
docker compose up --build -d              # Launch all services (Dagster UI at :3000)
```

### Database Initialization (first time, run against exposed DB on port 5433)
```bash
npx prisma db push                        # Apply schema
npx ts-node prisma/seed/seed.ts           # Seed TechStacks, Categories, etc.
```

### Python / Dagster
```bash
uv sync                                   # Install Python dependencies
dagster dev -h 0.0.0.0 -p 3000           # Run Dagster locally (outside Docker)
```

### dbt
```bash
cd dbt && dbt deps                        # Install dbt packages
dbt build                                 # Build all models
dbt run --select <model_name>             # Run a specific model
dbt test --select <model_name>            # Test a specific model
```
dbt profiles: `local` (default, port 5433) and `docker` (port 5432, host `db`). Set `DBT_TARGET` env var to switch.

### Linting & Type Checking
```bash
ruff check src/                           # Lint
ruff format src/                          # Format
mypy src/                                 # Type check (strict mode)
```

### Tests
```bash
pytest                                    # Run all tests (coverage included via --cov=src)
pytest tests/test_foo.py -k test_bar      # Run a single test
pytest -m unit                            # Run by marker (unit/integration/performance/api)
pytest -m integration                     # Dagster startup smoke test
```
Test config is in `pyproject.toml` under `[tool.pytest.ini_options]`. Tests use class-based style (`class TestXxx`).

Go tests:
```bash
cd src/services/go/fetcher && go test ./...   # Fetcher tests
cd src/services/go/scraper && go test ./...   # Scraper tests
```

### Go Binaries (must be compiled before local use)
```bash
cd src/services/go/scraper && go build -o github-scraper main.go
cd src/services/go/fetcher && go build -o ost-fetcher main.go
```
Set `GO_SCRAPER_PATH` and `GO_FETCHER_PATH` in `.env` to the compiled binary paths.

### Utility Scripts
```bash
scripts/go_binary_gen.sh                  # Compile Go binaries locally
scripts/clean_dagster.sh                  # Clear Dagster storage
scripts/sync_prisma.sh                    # Prisma schema sync
scripts/clean_docker_images.sh            # Docker image cleanup
```

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GITHUB_ACCESS_TOKEN` | GitHub fine-grained token for scraping |
| `OPENROUTER_API_KEY` | LLM classifier API key |
| `GO_SCRAPER_PATH` / `GO_FETCHER_PATH` | Paths to compiled Go binaries |
| `FASTTEXT_MODEL_PATH` | Path to `lid.176.ftz` (default: `models/lid.176.ftz`) |
| `DBT_TARGET` | dbt target profile (`local` by default, `docker` in container) |
| `DBT_PROJECT_DIR` | dbt project directory (default: `<repo>/dbt`, set to `/app/dbt` in Docker) |
| `DAGSTER_HOME` | Dagster metadata directory (default: `./dagster_home`) |

## Bug Fixing

When fixing a bug, always follow this order:
1. Write a failing test that reproduces the bug
2. Fix the code until the test passes
3. Never skip step 1 — no test, no fix

## Git Flow

`feature-branch` → `develop` (test) → `staging` (deploy) → `main` (release)

## CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `publish-prod.yml` | Release published | Docker build/push to `ghcr.io/opensource-together/ia` |
| `publish-develop.yml` | PR to main/staging + push to staging | Quality checks (reusable) + Docker build/push |
| `quality-checks.yml` | Reusable (`workflow_call`) | Lint, format, type check, tests, dbt, Go, Docker, Prisma, security |
| `claude-code-review.yml` | PR opened/synced (all branches) | Automatic Claude review (Sonnet) |
| `claude.yml` | `@claude` in issues/PR comments | AI assistant (requires workflow on default branch) |
| `sync-docs-submodule.yml` | PR to main/staging (path: `docs`) | Sync docs submodule to `ost-docs` repo |
| `sync-prisma-backend.yml` | PR to main/staging (path: `prisma/**`) | Sync Prisma schema to `ost-backend` repo |

**Important:** `claude.yml` uses `issue_comment`/`issues` events which only trigger from the **default branch** (`staging`). The workflow must exist on `staging` to work.

## Custom Agents (`.claude/agents/`)

| Agent | Model | Purpose |
|---|---|---|
| `dagster-reverse-cursed-technique` | opus | Dagster pipeline debugging and diagnostics |
| `dbt-six-eyes` | sonnet | dbt model review, debugging, and conventions |
| `security-prison-realm` | opus | Security audit (SQL injection, secrets, Docker, CI) |
| `go-black-flash` | sonnet | Go scraper/fetcher review (concurrency, rate limiting) |
| `infra-domain-expansion` | sonnet | Docker and CI/CD review (workflows, Dockerfile, compose) |
