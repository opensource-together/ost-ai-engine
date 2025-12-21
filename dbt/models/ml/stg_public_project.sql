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
    join {{ source('public', 'tech_stack') }} ts on pts."techStackId" = ts.id
    group by pts."projectId"
),

readmes as (
    select 
        repo_url,
        content
    from {{ source('ost', 'raw_github_readme') }}
)

select 
    p.id,
    p.title,
    p.description,
    p."repoUrl",
    coalesce(c.categories_list, '') as categories,
    coalesce(d.domains_list, '') as domains,
    coalesce(t.tech_stack_list, '') as tech_stack,
    coalesce(r.content, '') as readme,
    p."updatedAt"
from projects p
left join categories c on p.id = c."projectId"
left join domains d on p.id = d."projectId"
left join tech_stacks t on p.id = t."projectId"
left join readmes r on p."repoUrl" = r.repo_url
where p.published = true or p.trending = true
