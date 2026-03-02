with raw_user as (
    select * from {{ ref('int_user_enriched') }}
)

select
    user_id,
    {{ build_user_context([
        ('Full Name', 'name'),
        ('Bio', 'bio'),
        ('Job Title', 'job_title'),
        ('Tech Stacks', 'tech_stacks'),
        ('Domains', 'domains'),
        ('Interests', 'categories'),
        ('Experience', 'experiences::text')
    ]) }} as user_context
from raw_user
