with public_projects as (
    select * from {{ ref('stg_public__project') }}
),

contextualized as (
    select
        p.id,
        {{ build_project_context([
            ('Title', 'p.title'),
            ('Description', 'p.description'),
            ('Categories', 'p.categories'),
            ('Domains', 'p.domains'),
            ('Tech Stack', 'p.tech_stack'),
            ('Readme', clean_text('p.readme'))
        ]) }} as raw_context,
        now() as created_at
    from public_projects p
    where p.id is not null
)

select
    id,
    {{ clean_text('raw_context') }} as context,
    created_at
from contextualized
where raw_context is not null
and length(trim(raw_context)) > 10
