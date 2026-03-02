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
    inner join {{ ref('stg_github__project') }} p on s.project_id::uuid = p.id
),

deduped as (
    {{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
)

select id, project_id, repo_url, languages, created_at from deduped
