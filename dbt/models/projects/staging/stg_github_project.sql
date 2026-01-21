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
        data->>'language' as language,
        data->>'topics' as topics,
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

deduplicated as (
    select
        *,
        row_number() over (partition by url order by created_at desc) as rn
    from renamed
)

select
    id,
    name,
    description,
    url,
    stars,
    forks,
    language,
    topics,
    created_at,
    updated_at
from deduplicated
where rn = 1