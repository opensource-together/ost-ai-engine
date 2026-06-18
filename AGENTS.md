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

**What seed covers:** Prisma seed adds **taxonomies** (categories, domains, tech stacks) and **sample users**—not GitHub **`Project`** data, **embeddings**, or **dbt `match_*` tables**. For a **working stack without scraping first**, you still get a valid DB and can use **`/references`** and **`/health`**; project search, similarity, and trending need the **ingestion pipeline** (and typically **`dbt build`**) as documented in this file.

### Python / Dagster
```bash
uv sync                                   # Install Python dependencies
make dev                                  # Dagster UI on :3000 (uses workspace.host.yaml)
```

### REST API (FastAPI)
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000   # Run API locally
pytest tests/unit/api                              # Mocked API tests
```
The API is a lightweight, read-only service consumed by the [ost-mcp](https://github.com/opensource-together/ost-mcp) MCP server. It exposes project search, similarity, trending recommendations, and reference data.

### FastAPI service token (`OST_LINKER_*`)

Exact behavior (see `src/api/auth.py` and `lifespan` in `src/api/main.py`; covered by `tests/unit/api/test_service_token.py`). Business routes live under **`/v1/`**; **`/health`** stays unversioned.

| `OST_LINKER_REQUIRE_SERVICE_TOKEN` | `OST_LINKER_SERVICE_TOKEN` | Protected routes (`/projects`, `/references`, `/recommendations`, …) | `/health` |
| ---------------------------------- | -------------------------- | -------------------------------------------------------------------- | --------- |
| `false` or unset                    | unset or empty             | Open (no `X-Service-Token` required)                                  | Open      |
| `false` or unset                    | set                        | **401** unless `X-Service-Token` matches                               | Open      |
| `true`                             | unset or empty             | **Startup fails** (`RuntimeError` in lifespan)                        | n/a       |
| `true`                             | set                        | **401** unless header matches                                          | Open      |

**MCP-facing production:** set strict mode and a strong shared token; keep transport on a private network or TLS-terminated path so the header is not leaked.

### Postgres host bind (dev override)

Compose maps the dev database as `${POSTGRES_BIND_ADDR:-127.0.0.1}:${POSTGRES_PORT:-5433}:5432` (loopback-first by host port **5433** unless you override). Use `POSTGRES_BIND_ADDR=0.0.0.0` **only on trusted LANs** (e.g. DBeaver from another machine on Tailscale) and rely on `POSTGRES_PASSWORD` strength — see `.env.example`.

### Dagster: Docker vs host

- **Containers** use `-w /app/workspace.yaml` with `working_directory: /app` (bind-mounted tree).
- **Host** `make dev` uses `workspace.host.yaml` with `working_directory: .` so `src.linker.definitions` loads from your checkout. Keep both YAML files aligned if you rename modules.

### Ingestion / Dagster regression coverage

Not every ingestion asset ships full deterministic unit tests against Go binaries. After changing subprocess wiring (`raw_github__extract_projects`, trending, etc.), run a Dagster materialization smoke in dev or document manual rehearsal on the PR.

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
pytest tests/unit                                  # Unit tests (includes tests/unit/api/)
pytest -m integration                              # Dagster startup smoke test
pytest tests/integration/api                       # Live Postgres API tier (needs DATABASE_URL)
```
`make ci-check` runs ruff, sqlfluff, mypy, unit tests, and the Dagster smoke — aligned with `.github/workflows/ci.yml`. It does **not** run the Postgres tier; use **`make test-database`** when **`DATABASE_URL`** points at a migrated, seeded DB.

#### Verification tiers (CI vs local Postgres)

| Tier | Command | Needs |
| ---- | ------- | ----- |
| **Unit** | `pytest tests/unit --cov-fail-under=80` | Python only |
| **API mocks** | `tests/unit/api/` (included in unit tier) | Python only (mocked DB + semantic) |
| **Integration (Dagster)** | `pytest -m integration -k test_dagster_startup --no-cov` | Dagster env dirs (see workflow) |
| **Database** | `DATABASE_URL=... LINKER_SKIP_SEMANTIC_INIT=true make test-database` | Compose **db**, `npx prisma migrate deploy`, Prisma seed |

**`LINKER_SKIP_SEMANTIC_INIT`** — When set to **`true`**, FastAPI skips loading **`sentence-transformers`** (used in CI **`integration-db`** and **`tests/integration/api`**). Routes that call **`get_semantic()`** (e.g. **`/v1/projects/search-natural`**) stay untested in that mode.

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
| `API_RATE_LIMIT` | Requests per minute per IP (default `60`; applied by SlowAPI in `src/api/rate_limit.py`) |
| `OST_LINKER_SERVICE_TOKEN` | Optional header auth for the Linker API |
| `OST_LINKER_REQUIRE_SERVICE_TOKEN` | If true, API startup fails unless `OST_LINKER_SERVICE_TOKEN` is set (use in prod) |
| `API_ENABLE_OPENAPI` | If `true` (default), exposes `/openapi.json`, `/docs`, `/redoc`. Set `false` in production to hide schema and UIs. |

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
| `sync-docs-submodule.yml` | PR to main/staging (path: `ost-docs`) | Sync docs submodule to `ost-docs` repo |
| `sync-prisma-backend.yml` | PR to main/staging (path: `prisma/**`) | Sync Prisma schema to `ost-backend` repo |

**`ci.yml` notes:** CI runs lint, typecheck, unit tests, dbt compile, Go tests, integration-db, docker build, and pip-audit on PR/push to `develop`, `staging`, and `main`.
