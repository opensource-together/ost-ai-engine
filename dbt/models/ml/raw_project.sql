{{ config(materialized='table', schema='ml') }}

with public_projects as (
    select * from {{ ref('stg_public_project') }}
),

-- We need to join with raw_github_readme to get the readme content
-- Assuming there is a link via repoUrl or we can join on project_id if available.
-- public.Project has id, raw_github_readme has project_id (which might be the scraper ID, not the public ID).
-- BUT, core_public__sync_projects syncs scraper projects to public projects.
-- So we need to ensure we can join.
-- Actually, the user asked to source public.Project.
-- The README is in raw_github_readme (schema github).
-- Join condition: public.Project.repoUrl = raw_github_readme.repo_url (if unique)
-- OR we trust the sync process.

readmes as (
    select 
        repo_url,
        content
    from {{ source('ost', 'raw_github_readme') }}
)

select
    p.id,
    {{ generate_ml_context(
        'p.title',
        'p.description',
        'p.categories',
        'p.domains',
        'p.tech_stack',
        'r.content'
    ) }} as context,
    now() as created_at
from public_projects p
left join readmes r on p."repoUrl" = r.repo_url
where p.id is not null
