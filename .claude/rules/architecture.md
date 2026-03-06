# Architecture

## Multi-layer Pipeline (Dagster orchestrates everything)

The pipeline entry point is `src/linker/definitions.py`, which wires all assets, resources, jobs, schedules, and sensors into a single Dagster `Definitions` object. Dagster module is configured in `pyproject.toml` under `[tool.dagster]`.

**Data flow:**
```
GitHub API (Go scraper)                    [ingestion]
  -> raw DB tables (github schema)
  -> dbt staging/int models (github)       [ingestion]
  -> LLM classification                    [classification]
  -> public sync (public.Project)          [sync]
  -> dbt project ML prep (ml schema)       [ml_project_preparation]
  -> project embeddings (ml schema)        [ml]
  -> dbt matching models (public schema)   [matching]

User profiles (public.User)                [ml_user_preparation]
  -> dbt user ML prep (ml schema)
  -> user embeddings (ml schema)           [ml]
  -> dbt user matching (public schema)     [matching]
```

## Resources (`src/linker/resources/`)

| Resource | Purpose |
|---|---|
| `config_resource` (`PipelineConfig`) | Reads all env vars; injected as `"config"` |
| `LLMClassifierResource` | OpenRouter API (OpenAI-compatible) — uses `mistralai/mistral-small-3.2-24b-instruct` |
| `SentenceTransformerResource` | `all-MiniLM-L6-v2` for 384-dim embeddings; device defaults to `"cpu"` |
| `FastTextModelResource` | Language detection from `models/lid.176.ftz` |
| `PandasPostgresIOManager` | Custom IO manager passing DataFrames between assets via Postgres |

## Go Services (`src/services/go/`)

Two independent binaries, each with its own `go.mod`:
- `scraper/` — scrapes GitHub Search API, writes to `github.RawGithubProject`
- `fetcher/` — fetches per-repo details (README, languages, topics), writes to raw tables

Both are invoked as subprocesses by Dagster assets via `subprocess.run()`.

## Docker Build

3-stage Dockerfile:
1. **Go Builder** (`golang:1.24-alpine`) — compiles both Go binaries to `/app/bin/`
2. **Python Builder** (`python:3.11-slim`) — exports deps via uv to `requirements.txt`
3. **Runtime** (`python:3.11-slim`) — installs deps, copies Go binaries to `/usr/local/bin/`, runs Dagster

`docker-compose.yml` runs two services: `ost-linker` (app) and `db` (PostgreSQL with pgvector via `ankane/pgvector:v0.4.1`). DB is exposed on port 5433 by default.

## Database Schema

Managed by **Prisma** (`prisma/schema.prisma`) with 4 PostgreSQL schemas:
- `public` — user-facing models: `User`, `Project`, `Category`, `Domain`, `TechStack`, etc.
- `github` — raw scraped data: `RawGithubProject`, `RawGithubReadme`, `RawGithubLanguages`, `RawGithubTopics`, `IntGithubDetection`
- `ml` — ML artifacts: `EmbdGithubProject` (pgvector), `EmbdUser` (pgvector)
- `match` — computed recommendations (dbt materialized tables)

The `pgvector` extension enables cosine similarity search. The vector dimension is 384 (MiniLM-L6-v2).

Seed data lives in `prisma/seed/` (categories, domains, techstacks).

## Shared Utilities (`src/linker/utils/`)

- `language_detection.py` — `has_non_latin_chars()`, `parse_fasttext_labels()`, `is_blacklisted()` + constants (`NON_LATIN_LANGS`, `NON_LATIN_CHAR_RE`)
- `serialization.py` — `make_serializable()` (datetime/UUID → string), `clean_llm_json()` (strip markdown fences)

## Python Services (`src/services/python/`)

- `db.py` — shared DB cursor context manager (`get_db_cursor`) used by assets
