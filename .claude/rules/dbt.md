# dbt Layer (`dbt/`)

## Model Organization

Models are organized under `models/` by layer (flat structure):
- `staging/` — source-cleaning models (`stg_github__*`, `stg_public__*`)
- `intermediate/` — enrichment and transformation (`int_project_enriched`, `int_user_enriched`, `int_project_contextualized`, `int_project_embedding_candidate`)
- `marts/` — final consumption models (`fct_github_project`, `fct_public_user`, `match_global_recommendation`, `match_user_recommendation`)

## Profiles

dbt profiles: `local` (default, port 5433) and `docker` (port 5432, host `db`). Set `DBT_TARGET` env var to switch.

## Dagster Group Mapping

dbt models are assigned to Dagster groups via `+meta.dagster.group` in `dbt_project.yml`:
- `stg_github__*`, `int_project_enriched`, `fct_github_project` -> `ingestion`
- `stg_public__project`, `int_project_contextualized`, `int_project_embedding_candidate`, `match_global_recommendation` -> `project_ml`
- `stg_public__user`, `int_user_enriched`, `fct_public_user`, `match_user_recommendation` -> `user_ml`
