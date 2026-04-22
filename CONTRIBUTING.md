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
# Fill in DATABASE_URL, GITHUB_ACCESS_TOKEN, MISTRAL_API_KEY, paths, etc.

# 3. Install Python dependencies
uv sync

# 4. Compile Go binaries
bash scripts/go_binary_gen.sh

# 5. Start infrastructure
docker compose up --build -d

# 6. Initialize database
npx prisma db push
npx ts-node prisma/seed/seed.ts
```

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
uv run pytest tests/unit/test_cfg_resource.py -v
```

Tests are class-based (`class TestXxx`) and live under `tests/`.

## Linting & Formatting

```bash
ruff check src/       # Lint
ruff format src/      # Format
mypy src/             # Type-check
```

All lint and format checks must pass before opening a PR.

## Pull Request Process

1. Create a branch from `staging` (not `main`)
2. Make your changes with atomic commits
3. Ensure tests pass and lint is clean
4. Open a PR targeting `staging`
5. Request a review from `@spideystreet`

PR titles follow the same `<type>(<scope>): <summary>` format as commits.

## Getting Help

- [GitHub Issues](https://github.com/opensource-together/ost-linker/issues) — bug reports and feature requests
- [@spideystreet](https://x.com/spideystreet) — project updates
