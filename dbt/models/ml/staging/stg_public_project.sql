with public_projects as (
    select * from {{ ref('raw_public_project') }}
)

select
    p.id,
    {{ build_project_context([
        ('Title', 'p.title'),
        ('Description', 'p.description'),
        ('Categories', 'p.categories'),
        ('Domains', 'p.domains'),
        ('Tech Stack', 'p.tech_stack'),
        ('Readme', clean_text('p.readme'))
    ]) }} as context,
    now() as created_at
from public_projects p
where p.id is not null
