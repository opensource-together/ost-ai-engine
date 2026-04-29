This file provides guidance to agents when working with code in this repository.

## Project Overview

OST Linker is the AI-powered recommendation engine for [OpenSourceTogether](https://opensource-together.com/). It scrapes GitHub for open-source projects, classifies them via LLM, computes embeddings, and surfaces personalized recommendations to users via cosine similarity (pgvector).

## Common Commands

### Development Setup
```bash
cp .env.example .env                      # Configure environment
docker compose up --build -d              # Dev override: see `.env.example` for DAGSTER_HOST_PORT / LINKER_API_HOST_PORT
```

### Database Initialization (first time; host port = `POSTGRES_PORT` in `.env`, compose default **5433**)
From repo root, install Node deps once (`package.json` is committed): `npm ci`. Then:

```bash
npx prisma db push                        # Apply schema (DATABASE_URL must match POSTGRES_* / exposed port)
./node_modules/.bin/ts-node --compiler-options '{"module":"CommonJS"}' prisma/seed/seed.ts   # Seed (after npm install)
```
If `npx ts-node` fails on your Node version, use the `ts-node` line above from the repo root.

`make db-init` and `make dbt-build` source `./.env` when present so `DATABASE_URL` and Postgres-related vars match your compose/db setup.

### Python / Dagster
```bash
uv sync                                   # Install Python dependencies
dagster dev -h 0.0.0.0 -p 3000           # Run Dagster locally (outside Docker)
```

### REST API (FastAPI)
```bash
uvicorn src.services.api.main:app --host 0.0.0.0 --port 8000   # Run API locally
pytest -m api                                                    # Run API tests only
```
The API is a lightweight, read-only service consumed by the [ost-mcp](https://github.com/opensource-together/ost-mcp) MCP server. It exposes project search, similarity, trending recommendations, and reference data.

### dbt
Target `local` in `dbt/profiles.yml` uses `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `POSTGRES_DB` (defaults **ci_user** / **ci_pass** / **5433** if unset — wrong for your Docker DB). **Load the repo `.env` before running dbt:**

```bash
set -a && . ../.env && set +a            # from dbt/ ; or run from repo root after sourcing .env
cd dbt && dbt deps                        # Install dbt packages
dbt build                                 # Build all models
dbt run --select <model_name>             # Run a specific model
dbt test --select <model_name>            # Test a specific model
```
dbt profiles: `local` (host `POSTGRES_PORT` from env, often **5433** from compose) and `docker` (port **5432**, host `db`). Set `DBT_TARGET` env var to switch.

Source freshness (pipeline staleness): configured in `dbt/models/sources.yml` for key `github`, `match`, `ml`, and `public.Project` tables. Run `dbt source freshness` (after `dbt deps` if needed) against a DB that matches your `profiles.yml` target.

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
Set `GO_SCRAPER_PATH`, `GO_FETCHER_PATH`, and (if used) `GO_TRENDING_PATH` in `.env` to the compiled binary paths.

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
| `DATABASE_URL` | PostgreSQL connection string (must match `POSTGRES_*` when using compose DB) |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Compose `db` service + host tools (default published port **5433** unless overridden) |
| `GITHUB_ACCESS_TOKEN` | GitHub fine-grained token for scraping |
| `MISTRAL_API_KEY` | LLM classifier API key (Mistral AI) |
| `GO_SCRAPER_PATH` / `GO_FETCHER_PATH` / `GO_TRENDING_PATH` | Paths to compiled Go binaries (trending used when configured) |
| `FASTTEXT_MODEL_PATH` | Path to `lid.176.ftz` (default: `models/lid.176.ftz`) |
| `DBT_TARGET` | dbt target profile (`local` by default, `docker` in container) |
| `DBT_PROJECT_DIR` | dbt project directory (default: `<repo>/dbt`, set to `/app/dbt` in Docker) |
| `DAGSTER_HOME` | Dagster config directory (`dagster.yaml`); Docker: `/app/dagster_home` on the data volume |
| `DAGSTER_STORAGE_DIR` | SQLite instance storage (Docker: `/app/dagster_home/storage`; see `dagster.yaml`) |
| `DAGSTER_LOGS_DIR` | Compute logs base dir (Docker: `/app/dagster_home/logs`) |
| `DAGSTER_HOST_PORT` | Optional: host port mapped to Dagster UI (**3000** if unset; see `.env.example` for dev conflicts) |
| `LINKER_API_HOST_PORT` | Optional: host port mapped to FastAPI (**8000** if unset; set MCP `OST_API_URL` to match when changed) |
| `API_HOST` | API listen host inside container (default `0.0.0.0`) |
| `API_PORT` | API listen port inside container (default `8000`) |
| `API_RATE_LIMIT` | Requests per minute per IP (default `60`) |
| `OST_LINKER_SERVICE_TOKEN` | Optional header auth for the Linker API |
| `OST_LINKER_REQUIRE_SERVICE_TOKEN` | If true, API startup fails unless `OST_LINKER_SERVICE_TOKEN` is set (use in prod) |

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
| `sync-docs-submodule.yml` | PR to main/staging (path: `ost-docs`) | Sync docs submodule to `ost-docs` repo |
| `sync-prisma-backend.yml` | PR to main/staging (path: `prisma/**`) | Sync Prisma schema to `ost-backend` repo |

**`quality-checks.yml` notes:** the security job runs `gitleaks detect --no-git`, which scans the **checked-out tree only** (not full `git` history)—a fast working-tree leak check. On **fork pull requests**, the `docs-submodule` job is skipped when the PR head is another repository, because org secrets are not available to those runs. The same fork guard applies to **`sync-docs-submodule.yml`** and **`sync-prisma-backend.yml`** (entire job skipped for fork PRs).

**Important:** `claude.yml` uses `issue_comment`/`issues` events which only trigger from the **default branch** (`staging`). The workflow must exist on `staging` to work.
