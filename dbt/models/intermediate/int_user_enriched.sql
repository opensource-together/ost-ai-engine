with user_base as (
    select * from {{ ref('stg_public__user') }}
),

tech_stacks as (
    select 
        uts."userId" as user_id,
        string_agg(ts.name, ', ') as tech_stack_list
    from {{ source('public', 'user_tech_stack') }} uts
    join {{ source('public', 'tech_stack') }} ts on uts."techStackId" = ts.id
    group by uts."userId"
),

domains as (
    select 
        ud."userId" as user_id,
        string_agg(d.name, ', ') as domain_list
    from {{ source('public', 'user_domain') }} ud
    join {{ source('public', 'Domain') }} d on ud."domainId" = d.id
    group by ud."userId"
),

categories as (
    select 
        uc."userId" as user_id,
        string_agg(c.name, ', ') as category_list
    from {{ source('public', 'user_categories') }} uc
    join {{ source('public', 'Category') }} c on uc."categoryId" = c.id
    group by uc."userId"
)

select
    u.user_id,
    u.name,
    u.bio,
    u.job_title,
    u.experiences,
    coalesce(t.tech_stack_list, '') as tech_stacks,
    coalesce(d.domain_list, '') as domains,
    coalesce(c.category_list, '') as categories
from user_base u
left join tech_stacks t on u.user_id = t.user_id
left join domains d on u.user_id = d.user_id
left join categories c on u.user_id = c.user_id
