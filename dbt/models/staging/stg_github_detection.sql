with source as (
    select * from {{ source('ost', 'raw_github_detection') }}
),

deduplicated as (
    select
        id,
        project_id,
        repo_url,
        language_detected,
        language_confidence,
        created_at,
        row_number() over (partition by project_id order by created_at desc) as rn
    from source
)

select
    id,
    project_id,
    repo_url,
    language_detected,
    language_confidence,
    created_at
from deduplicated
where rn = 1
