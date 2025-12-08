with enriched as (
    select * from {{ ref('int_github_project_enriched') }}
)

select
    id,
    name,
    description,
    url,
    stars,
    forks,
    created_at,
    updated_at,
    readme_content as readme,
    fetched_topics as topics,
    fetched_languages as languages,
    language_detected,
    language_confidence,
    primary_language as language
from enriched
