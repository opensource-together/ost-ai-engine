Recommender-system of the [OpenSource Together](https://github.com/opensource-together) platform.  

<div align="center">

<img width="100%" alt="ost-knight" src="https://github.com/user-attachments/assets/cdf66f76-89bf-4150-b798-e26a25dc8239" />

[![Discord](https://img.shields.io/badge/Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/4ZDhm3dQAC) [![Follow](https://img.shields.io/twitter/follow/OpenSTogether?style=social)](https://x.com/OpenSTogether) [![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL--v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

</div>

---

## What is OST Linker?

The AI-powered recommendation engine behind [OpenSourceTogether](https://opensource-together.com/). It scrapes GitHub, classifies projects via LLM, builds embeddings, and serves personalized recommendations through a read-only FastAPI consumed by [ost-mcp](https://github.com/opensource-together/ost-mcp).

## Architecture

```
GitHub / Trending (Go) → Postgres (raw) → Dagster + dbt → embeddings + match_* marts
                                                              ↓
                                                    FastAPI /v1/* (ost-mcp)
```

| Component | Role |
| --- | --- |
| Dagster | Batch pipeline (scrape, classify, embed, dbt) |
| dbt | Warehouse models (`stg_`, `int_`, `fct_`, `match_*`) |
| FastAPI (`src/api/`) | Read-only HTTP API; `/health` unversioned; business routes under `/v1/` |
| Postgres + pgvector | Storage and similarity search |

## Quickstart

```bash
cp .env.example .env              # DATABASE_URL, tokens, optional host ports
make setup                        # uv sync + Go binaries (data/)
npm ci
docker compose up --build -d      # Dagster + API + db
make db-init                      # Prisma schema + seed
curl -f http://127.0.0.1:${LINKER_API_HOST_PORT:-8000}/health
make ci-check                     # lint, types, unit tests (see CONTRIBUTING.md)
```

## Key environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres connection (must match compose `POSTGRES_*`) |
| `OST_LINKER_SERVICE_TOKEN` | Shared API key for `/v1/*` (header `X-Service-Token`) |
| `OST_LINKER_REQUIRE_SERVICE_TOKEN` | If `true`, startup fails without token |
| `GITHUB_ACCESS_TOKEN` | GitHub API (Dagster pipeline only) |
| `MISTRAL_API_KEY` | LLM classification (pipeline only) |
| `GO_*_PATH` | Compiled Go binary paths |
| `LINKER_API_HOST_PORT` | Host port for API (default 8000) |

See [`.env.example`](.env.example) and [AGENTS.md](AGENTS.md) for the full list.

Business routes are under **`/v1/`** (e.g. `/v1/projects/search`). **`/health`** stays unversioned.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Operator runbook: [AGENTS.md](AGENTS.md).

## License

[GNU Affero General Public License v3.0 only (AGPL-3.0-only)](https://www.gnu.org/licenses/agpl-3.0.html) — [LICENSE](LICENSE).
