with user_vectors as (
    select 
        "userId" as user_id, 
        "vector" 
    from {{ source('ml', 'embd_user') }}
),

project_vectors as (
    select 
        "projectId" as project_id, 
        "vector" 
    from {{ source('ml', 'embd_github_project') }}
),

recommendations as (
    select
        u.user_id,
        p.project_id,
        1 - (u.vector <=> p.vector) as similarity_score
    from user_vectors u
    cross join lateral (
        select 
            project_id, 
            vector
        from project_vectors p
        order by u.vector <=> p.vector
        limit 50
    ) p
)

select
    user_id,
    project_id,
    similarity_score,
    now() as calculated_at
from recommendations
where similarity_score > 0.30
