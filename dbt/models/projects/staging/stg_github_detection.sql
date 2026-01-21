with source as (
    select * from {{ source('github', 'int_github_detection') }}
),

cleaned as (
    select
        s.id,
        s.project_id::uuid as project_id,
        s.repo_url,
        s.language_detected,
        s.language_confidence,
        s.created_at
    from source s
    inner join {{ ref('stg_github_project') }} p on s.project_id::uuid = p.id
)

{{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
