with source as (
    select * from {{ source('github', 'int_github_detection') }}
),

cleaned as (
    select
        id,
        project_id::uuid as project_id,
        repo_url,
        language_detected,
        language_confidence,
        created_at
    from source
)

{{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
