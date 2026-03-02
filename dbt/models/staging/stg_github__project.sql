with source as (
    select * from {{ source('github', 'raw_github_project') }}
),

renamed as (
    select
        id,
        data->>'name' as name,
        data->>'description' as description,
        data->>'html_url' as url,
        (data->>'stargazers_count')::int as stars,
        (data->>'forks_count')::int as forks,
        (data->>'open_issues_count')::int as open_issues_count,
        data->>'language' as language,
        (data->>'pushed_at')::timestamp as pushed_at,
        "createdAt" as created_at,
        "updatedAt" as updated_at
    from source
    where
        -- Filter out projects with empty descriptions (logic from core_github__extract_top_projects)
        data->>'description' is not null
        and length(trim(data->>'description')) > 0
        -- Filter out projects with no language (optional, but good practice if we filter by language later)
        and data->>'language' is not null
),

deduped as (
    {{ deduplicate('renamed', 'url', 'created_at desc') }}
)

select id, name, description, url, stars, forks, open_issues_count, language, pushed_at, created_at, updated_at
from deduped
