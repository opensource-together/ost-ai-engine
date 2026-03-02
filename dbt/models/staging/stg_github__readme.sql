with source as (
    select * from {{ source('github', 'raw_github_readme') }}
),

cleaned as (
    select
        s.id,
        s.project_id::uuid as project_id,
        s.repo_url,
        s.content,
        s.created_at
    from source s
    inner join {{ ref('stg_github__project') }} p on s.project_id::uuid = p.id
    where s.content is not null
),

deduped as (
    {{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
)

select id, project_id, repo_url, content, created_at from deduped
