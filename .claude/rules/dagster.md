# Dagster

## Asset Groups (`src/linker/`)

| Group | Asset(s) | Description |
|---|---|---|
| `ingestion` | `raw_github__extract_projects` + 4 fetcher assets + dbt staging/int/mart GitHub | Go binaries write raw data; Python fetchers enrich it |
| `classification` | `core_match__classify_projects` | LLM via OpenRouter classifies projects into Category + Domain |
| `sync` | `core_public__sync_projects` | Syncs enriched data into public-facing `Project` table |
| `project_ml` | (dbt) `stg_public__project`, `int_project_contextualized`, `int_project_embedding_candidate`, `match_global_recommendation` + (Python) `core_ml__embed_projects` | Project ML prep, embeddings, and global recommendations |
| `user_ml` | (dbt) `stg_public__user`, `int_user_enriched`, `fct_public_user`, `match_user_recommendation` + (Python) `core_ml__embed_users` | User ML prep, embeddings, and user recommendations |

## Jobs

- `project_enrichment_job` — classification + sync + project_ml (scheduled 1x daily at 3 AM Europe/Paris, with retry policy)
- `project_scraper_job` — ingestion only (manual, with retry policy)
- `user_recommendation_job` — user_ml (scheduled every 10min)
- `run_all_job` — all groups (manual, for init/recovery)
- `cleanup_dagster_history_job` — housekeeping (scheduled every 2 days at 23h)

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
