{{ config(materialized='view', schema='ml') }}

with projects as (
    select * from {{ source('public', 'Project') }}
),

categories as (
    select 
        pc."projectId",
        string_agg(c.name, ', ') as categories_list
    from {{ source('public', 'project_category') }} pc
    join {{ source('public', 'Category') }} c on pc."categoryId" = c.id
    group by pc."projectId"
),

domains as (
    select 
        pd."projectId",
        string_agg(d.name, ', ') as domains_list
    from {{ source('public', 'project_domain') }} pd
    join {{ source('public', 'Domain') }} d on pd."domainId" = d.id
    group by pd."projectId"
),

tech_stacks as (
    select 
        pts."projectId",
        string_agg(ts.name, ', ') as tech_stack_list
    from {{ source('public', 'project_tech_stack') }} pts
    join {{ source('public', 'TechStack') }} ts on pts."techStackId" = ts.id
    group by pts."projectId"
)

select 
    p.id,
    p.title,
    p.description,
    p."repoUrl",
    coalesce(c.categories_list, '') as categories,
    coalesce(d.domains_list, '') as domains,
    coalesce(t.tech_stack_list, '') as tech_stack,
    -- We can fetch README via raw_github_readme later if needed, but the user asked for context here.
    -- Assuming we might join raw_github_readme here or later. The user mentioned "sourcing public.Project".
    -- Let's stick to public schema for this Staging.
    p."updatedAt"
from projects p
left join categories c on p.id = c."projectId"
left join domains d on p.id = d."projectId"
left join tech_stacks t on p.id = t."projectId"
where p.published = true or p.trending = true
