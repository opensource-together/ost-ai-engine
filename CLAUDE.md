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
poetry install                            # Install Python dependencies
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
```
Test config is in `pyproject.toml` under `[tool.pytest.ini_options]`. Tests use class-based style (`class TestXxx`).

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

## CI/CD

- `publish-prod.yml` — on release, pushes Docker image to `ghcr.io/opensource-together/ia`
- `publish-develop.yml` — develop branch deployment
- `deploy-docs.yml` — auto-syncs `docs/ai/**` to external docs repo
