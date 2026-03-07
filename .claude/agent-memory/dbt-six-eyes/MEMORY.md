# dbt-six-eyes Agent Memory

## Critical: Dagster Group Names (verified against dbt_project.yml)

The system prompt lists old group names — the ACTUAL groups in `dbt_project.yml` are:
- `ingestion` — stg_github__*, int_project_enriched, fct_github_project
- `project_ml` — stg_public__project, int_project_contextualized, int_project_embedding_candidate, match_global_recommendation
- `user_ml` — stg_public__user, int_user_enriched, fct_public_user, match_user_recommendation

The system prompt references `ml_preparation` and `matching` — these are STALE names.

## Schema Mapping (verified against dbt_project.yml)

| Model | Schema |
|-------|--------|
| stg_github__* | github |
| stg_public__user | ml |
| stg_public__project | ml |
| int_project_enriched | github |
| int_user_enriched | ml |
| int_project_contextualized | ml |
| int_project_embedding_candidate | ml |
| fct_github_project | github |
| fct_public_user | ml |
| match_global_recommendation | public |
| match_user_recommendation | public |

NOTE: match_* models write to `public` schema, NOT `match` schema.
The `match` schema exists in Prisma but NO dbt model writes to it.

## Known Documentation Errors (docs/ai/)

- `structure.mdx:82` — claims `match` schema holds "dbt-materialized tables"; wrong, dbt writes match_* to `public`
- `overview.mdx:37` — dbt card says "4 PostgreSQL schemas"; dbt actually uses 3 (github, ml, public)

## Macros Present (dbt/macros/)

build_project_context, build_user_context, clamp, clean_text, deduplicate,
generate_schema_name, jsonb_to_list, safe_divide

## Custom Tests (dbt/tests/)

unique_user_project_recommendation, valid_hybrid_score_bounds

## All Materializations

All models (staging, intermediate, marts) are `table` in dbt_project.yml.
No intermediates use `view` despite the known-issue recommendation.
