# Contributing to OST Linker

OST Linker is the intelligent recommender-system of [OpenSourceTogether](https://opensource-together.com/). Contributions are welcome — bug fixes, new features, tests, and documentation improvements. **By contributing, you agree that your contributions will be licensed under the [GNU AGPL-3.0-only](LICENSE), the same license as this repository** (strong copyleft).

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
uv run pytest tests/unit              # Unit tests (with coverage)
uv run pytest tests/integration       # Integration (Dagster smoke + live DB when DATABASE_URL set)
make test-database                    # Postgres-backed API tests (needs migrated + seeded DB)
cd src/services/go/scraper && go test ./...
cd src/services/go/fetcher && go test ./...
cd src/services/go/trending && go test ./...
uv run pytest -m integration -k test_dagster_startup --no-cov
```

Tests mirror `src/` under `tests/unit/` and `tests/integration/`. Class-based style (`class TestXxx`).

More detail: [AGENTS.md](AGENTS.md).

## Linting & Formatting

```bash
uv run ruff check src/
uv run ruff format src/
uv run mypy src/
uv run sqlfluff lint dbt/
```

**`make ci-check`** covers ruff, format, mypy, unit tests, and the Dagster smoke. Sqlfluff and `dbt build` run in CI (`lint` / `dbt-build`); locally use **`make ci-check-full`** when `DATABASE_URL` is set.

## PR checklist

- [ ] Tests for new/changed behavior
- [ ] `make ci-check` passes locally
- [ ] No secrets in code or commits
- [ ] Target branch: `develop`

### Optional: pre-commit

After `uv sync`, install Git hooks so staged Python files match CI before you commit:

```bash
uv run pre-commit install
```

## Pull Request Process

1. Create a branch from `develop`
2. Make your changes with atomic commits
3. Run **`make ci-check`**
4. Open a PR targeting **`develop`**
5. Request a review from `@spideystreet`

PR titles follow the same `<type>(<scope>): <summary>` format as commits.

## Getting Help

- [GitHub Issues](https://github.com/opensource-together/ost-linker/issues) — bug reports and feature requests
- [@spideystreet](https://x.com/spideystreet) — project updates
