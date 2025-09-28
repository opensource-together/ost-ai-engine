-- Minimal staging model pulling from raw ingest table
select
  uuid,
  platform,
  external_id,
  name,
  full_name,
  description,
  html_url,
  homepage,
  default_branch,
  visibility,
  language,
  topics,
  license,
  stars,
  forks,
  open_issues,
  subscribers,
  archived,
  owner,
  namespace,
  created_at_source,
  updated_at_source,
  last_activity_at_source,
  _loaded_at
from {{ source('trending', 'stg_trending_projects') }}

