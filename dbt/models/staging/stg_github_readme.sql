with source as (
    select * from {{ source('ost', 'raw_github_readme') }}
),

deduplicated as (
    select
        id,
        project_id,
        repo_url,
        content,
        created_at,
        row_number() over (partition by project_id order by created_at desc) as rn
    from source
)

select
    id,
    project_id,
    repo_url,
    content,
    created_at
from deduplicated
where rn = 1
