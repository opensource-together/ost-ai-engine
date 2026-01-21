with source as (
    select * from {{ source('github', 'raw_github_languages') }}
),

cleaned as (
    select
        s.id,
        s.project_id::uuid as project_id,
        s.repo_url,
        s.languages,
        s.created_at
    from source s
    inner join {{ ref('stg_github_project') }} p on s.project_id::uuid = p.id
)

{{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
