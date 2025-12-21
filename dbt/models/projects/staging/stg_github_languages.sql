with source as (
    select * from {{ source('github', 'raw_github_languages') }}
),

cleaned as (
    select
        id,
        project_id::uuid as project_id,
        repo_url,
        languages,
        created_at
    from source
)

{{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
