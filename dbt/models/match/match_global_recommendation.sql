
with projects as (
    select * from {{ source('public', 'Project') }}
),

metadata as (
    select * from {{ ref('pvt_github_project') }}
),

final as (
    select
        p.id as project_id,
        m.stars,
        p."updatedAt" as last_synced_at
    from projects p
    inner join metadata m on p.id::uuid = m.id
    where p.trending = true
    order by p."updatedAt" desc, m.stars desc
    limit 5
)

select * from final
