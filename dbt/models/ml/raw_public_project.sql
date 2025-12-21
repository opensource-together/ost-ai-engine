with public_projects as (
    select * from {{ ref('stg_public_project') }}
)

select
    p.id,
    {{ generate_ml_context(
        'p.title',
        'p.description',
        'p.categories',
        'p.domains',
        'p.tech_stack',
        'p.readme'
    ) }} as context,
    now() as created_at
from public_projects p
where p.id is not null
