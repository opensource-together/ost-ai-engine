# dbt Layer (`dbt/`)

## Model Organization

Models are organized under `models/` by domain:
- `projects/` — staging -> int -> pivot for raw GitHub data (`github` schema)
- `ml/` — staging -> int for embedding candidates (`ml` schema)
- `users/` — staging -> int -> pivot for user data (`ml` schema)
- `match/` — final recommendation tables (`public` schema):
  - `match_user_recommendation.sql` — cosine similarity via pgvector `<=>` operator
  - `match_global_recommendation.sql` — trending projects

## Profiles

dbt profiles: `local` (default, port 5433) and `docker` (port 5432, host `db`). Set `DBT_TARGET` env var to switch.

## Dagster Group Mapping

dbt models are assigned to Dagster groups via `+meta.dagster.group` in `dbt_project.yml`:
- `projects/` models -> `ingestion`
- `ml/` and `users/` models -> `ml_preparation`
- `match/` models -> `matching`
