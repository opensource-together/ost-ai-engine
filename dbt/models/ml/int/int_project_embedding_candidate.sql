
with projects as (
    select * from {{ source('public', 'Project') }}
),

classifications as (
    select * from {{ source('match', 'project_classification') }}
),

categories as (
    select * from {{ source('public', 'Category') }}
),

domains as (
    select * from {{ source('public', 'Domain') }}
),

original_context as (
    select id, context from {{ ref('pvt_github_project') }}
),

enriched as (
    select
        p.id as project_id,
        p.title,
        p.description,
        p."updatedAt",
        -- Construct richer context combining original raw data + classification results
        concat(
            coalesce(oc.context, ''), 
            ' | Category: ', coalesce(c.name, 'Uncategorized'),
            ' | Domain: ', coalesce(d.name, 'General')
        ) as rich_context_string,
        row_number() over (order by p."updatedAt" desc) as rn
    from projects p
    left join classifications cl on p.id = cl."projectId"
    left join categories c on cl."categoryId" = c.id
    left join domains d on cl."domainId" = d.id
    left join original_context oc on p.id::uuid = oc.id
    where p.published = true or p.trending = true
)

select
    project_id,
    rich_context_string
from enriched
where rn <= 50 -- Top X limit of projects to embed for recommendations
