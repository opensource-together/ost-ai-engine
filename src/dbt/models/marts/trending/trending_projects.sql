{{
  config(
    materialized='incremental',
    unique_key=['uuid'],
    on_schema_change='append_new_columns',
    post_hook=[
      "CREATE UNIQUE INDEX IF NOT EXISTS idx_trending_projects_uuid ON {{ this }} (uuid)"
    ]
  )
}}

with src as (
  select
    uuid,
    platform,
    external_id as externalId,
    name,
    full_name as fullName,
    description,
    html_url as htmlUrl,
    homepage,
    default_branch as defaultBranch,
    visibility,
    language,
    topics,
    license,
    stars,
    forks,
    open_issues as openIssues,
    subscribers,
    archived,
    owner,
    namespace,
    created_at_source as createdAtSource,
    updated_at_source as updatedAtSource,
    last_activity_at_source as lastActivityAtSource
  from {{ ref('stg_trending_projects') }}
)

select src.*
from src
{% if is_incremental() %}
left join (
  select coalesce(max(updatedAtSource), max(createdAtSource)) as last_ts
  from {{ this }}
) as latest on true
-- Only upsert rows newer than the latest seen
where coalesce(src.updatedAtSource, src.createdAtSource) > coalesce(latest.last_ts, to_timestamp(0))
{% endif %}


