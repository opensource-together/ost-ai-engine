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

- `run_all_job` — runs all asset groups (scheduled 1x daily at 3 AM Europe/Paris)
- `project_scraper_job` — ingestion only (with retry policy)
- `project_classification_job` — classification + sync (triggered by sensor after scraper succeeds, with retry policy)
- `project_embedding_job` — ml_preparation + ml + matching
- `user_recommendation_job` — user embeddings + matching + sync (scheduled every 2h)
- `cleanup_dagster_history_job` — housekeeping (scheduled every 2 days at 23h)

## Sensor

`classification_sensor` triggers `project_classification_job` on scraper success.

## Asset Naming Convention

**Python Dagster assets** follow a `<layer>_<source>__<description>` pattern:
- `raw_github__*` — raw ingestion
- `core_github__*` — enriched GitHub data
- `core_match__*` — matching/classification
- `core_ml__*` — ML/embedding assets
- `core_public__*` — public-facing sync

**dbt models** follow a flat layer-first layout (`models/staging/`, `models/intermediate/`, `models/marts/`):
- Staging: `stg_<source>__<entity>` (double underscore)
- Intermediate: `int_<entity>_<verb/description>`
- Marts: `fct_<entity>`, `dim_<entity>`, or `<entity>`

dbt models in Dagster use their schema + model name as `AssetKey`, e.g., `AssetKey(["github", "stg_github__project"])`.
