# Contributing to OST Linker

OST Linker is the AI-powered recommendation engine of [OpenSourceTogether](https://opensource-together.com/). Contributions are welcome — bug fixes, new features, tests, and documentation improvements.

## Prerequisites

| Tool | Version |
| :--- | :--- |
| Python | 3.11 |
| Go | 1.24+ |
| Docker & Docker Compose | latest |
| Node.js | v18+ |
| uv | latest |

## Local Setup

```bash
# 1. Fork then clone
git clone https://github.com/<your-fork>/ost-linker.git
cd ost-linker

# 2. Configure environment
cp .env.example .env
# Fill in DATABASE_URL (match POSTGRES_* / port from compose, often 5433), GITHUB_ACCESS_TOKEN,
# MISTRAL_API_KEY, GO_* paths, etc. See AGENTS.md for the full variable list.

# 3. Install dependencies
uv sync
npm ci

# 4. Compile Go binaries (or: make build-go)
bash scripts/go_binary_gen.sh

# 5. Start infrastructure
docker compose up --build -d

# 6. Initialize database (loads .env when present; uses CommonJS for seed)
make db-init
```

Equivalent manual steps if you prefer not to use Make:

```bash
npx prisma db push
./node_modules/.bin/ts-node --compiler-options '{"module":"CommonJS"}' prisma/seed/seed.ts
```

If `npx ts-node` misbehaves on your Node version, use the `ts-node` line above from the repo root after `npm ci`. You can also run **`npx prisma db seed`** after `db push` (same script as `make db-init`).

**Seed vs pipeline:** Prisma seed fills **reference data** (categories, domains, tech stacks, sample users)—not **`Project`** rows, embeddings, or **`match_*`** marts. You can run the **API + DB** and hit **`/health`** and **`/references/*`** without scraping; **search, similar projects, and trending** need Dagster/Go ingest and usually **`make dbt-build`** (see [AGENTS.md](AGENTS.md)).

**Shortcut:** `make setup` runs `uv sync` and compiles Go binaries; then run `npm ci`, `docker compose up`, and `make db-init`.

## Branch Naming

```
feat/<short-description>     # New features
fix/<short-description>      # Bug fixes
refactor/<short-description> # Refactoring
test/<short-description>     # Tests only
docs/<short-description>     # Documentation
chore/<short-description>    # Tooling, deps, CI
```

Never commit directly to `main` or `staging`.

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<scope>): <imperative summary>
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

**Scopes:**

| Scope | Covers |
| :--- | :--- |
| `resources` | `src/linker/resources/` |
| `assets` | `src/linker/assets/` |
| `linker` | General pipeline / definitions |
| `dbt` | `dbt/` models |
| `scraper` | Go scraper binary |
| `fetcher` | Go fetcher binary |
| `infra` | Docker, CI, scripts |

Examples:
```
feat(assets): add core_ml__embed_users asset
fix(resources): resolve null pointer in LLM classifier
refactor(linker): migrate PipelineConfig fields to EnvVar
test(resources): add unit tests for build_scraper_env
```

## Running Tests

```bash
uv run pytest                     # All tests (with coverage)
uv run pytest -m unit             # Unit tests only
uv run pytest -m api              # FastAPI tests only
uv run pytest tests/unit/test_cfg_resource.py -v
```

Tests are class-based (`class TestXxx`) and live under `tests/`. Dagster integration smoke: `uv run pytest -m integration`.

More detail: [AGENTS.md](AGENTS.md) (commands, dbt, CI notes).

## Linting & Formatting

```bash
uv run ruff check src/       # Lint
uv run ruff format src/      # Format
uv run mypy src/             # Type-check
```

All lint and format checks must pass before opening a PR (CI runs these via `uv run`). **`make ci-check`** runs the same Python steps as the **quality** job in [`.github/workflows/quality-checks.yml`](.github/workflows/quality-checks.yml) (ruff, mypy, unit + api + Dagster smoke).

### Optional: pre-commit

After `uv sync`, install Git hooks so staged Python files match CI before you commit:

```bash
uv run pre-commit install
```

## Pull Request Process

1. Create a branch from `staging` (not `main`)
2. Make your changes with atomic commits
3. Run **`make ci-check`** (or match the **Linting & formatting** + **Running tests** sections above)
4. Open a PR targeting `staging`
5. Request a review from `@spideystreet`

PR titles follow the same `<type>(<scope>): <summary>` format as commits.

## Getting Help

- [GitHub Issues](https://github.com/opensource-together/ost-linker/issues) — bug reports and feature requests
- [@spideystreet](https://x.com/spideystreet) — project updates
