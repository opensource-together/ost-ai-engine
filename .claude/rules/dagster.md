# Dagster

## Asset Groups (`src/linker/`)

| Group | Asset(s) | Description |
|---|---|---|
| `ingestion` | `raw_github__extract_projects` + 4 fetcher assets | Go binaries write raw data; Python fetchers enrich it |
| `classification` | `core_match__classify_projects` | LLM via OpenRouter classifies projects into Category + Domain |
| `ml` | `core_ml__embed_projects`, `core_ml__embed_users` | SentenceTransformer embeds projects & users |
| `sync` | `core_public__sync_projects` | Syncs enriched data into public-facing `Project` table |
| `dbt_models` | all dbt models | Runs `dbt build` via `dagster-dbt` |

## Jobs

- `run_all_job` — runs all assets (scheduled 5x daily Europe/Paris)
- `project_scraper_job` — ingestion only
- `project_classification_job` — triggered by sensor after scraper succeeds
- `project_embedding_job` — ML embedding
- `cleanup_dagster_history_job` — housekeeping

## Sensor

`classification_sensor` triggers `project_classification_job` on scraper success.

## Asset Naming Convention

Assets follow a `<layer>_<source>__<description>` pattern:
- `raw_github__*` — raw ingestion
- `core_github__*` — enriched GitHub data
- `core_match__*` — matching/classification
- `core_ml__*` — ML/embedding assets
- `core_public__*` — public-facing sync

dbt models in Dagster use their schema + model name as `AssetKey`, e.g., `AssetKey(["github", "pvt_github_project"])`.
