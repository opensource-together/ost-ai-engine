# dbt Analyst Memory

## Key Fixes Applied (confirmed working)

- **profiles.yml local target**: `POSTGRES_USER` and `POSTGRES_PASSWORD` must use `env_var(...)` with NO fallback default. The docker target intentionally keeps empty-string defaults — do not change those.
- **match_user_recommendation.sql user_totals CTE**: use pre-aggregated subqueries (GROUP BY inside LEFT JOIN subquery) to avoid O(n³) row explosion from joining raw junction tables directly.
- **freshness_score**: always clamp both bounds — `greatest(0, least(1.0, ...))`. Missing the upper `least(1.0, ...)` is a confirmed bug when `pushed_at` is in the future.

## dbt parse workflow

Run `dbt parse` to validate SQL without a live DB:
```bash
cd dbt && POSTGRES_USER=test POSTGRES_PASSWORD=test uv run dbt parse --profiles-dir .
```
`--profiles-dir .` tells dbt to read `dbt/profiles.yml` rather than `~/.dbt/profiles.yml`.
Since `POSTGRES_USER`/`POSTGRES_PASSWORD` have no defaults in the local profile (by design), dummy env vars are needed to pass parsing.

## Known open issues (not yet fixed)

- No `relationships` tests on any FK columns across all models
- No source freshness configured (`loaded_at_field` / `freshness` in sources.yml)
- `stg_public__project.sql:53` UUID namespace mismatch risk between `Project.id` and github `project_id`
- All models materialized as `table` — intermediates should be `view` unless perf requires otherwise
