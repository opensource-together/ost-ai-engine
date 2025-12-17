
with users as (
    select * from {{ ref('stg_public_user') }}
),

tech_stacks as (
    select
        uts.user_id,
        string_agg(ts.name, ', ') as tech_stacks_list
    from {{ ref('stg_public_user_tech_stack') }} uts
    join {{ ref('stg_public_tech_stack') }} ts on uts.tech_stack_id = ts.id
    group by uts.user_id
),

domains as (
    select
        ud.user_id,
        string_agg(d.name, ', ') as domains_list
    from {{ ref('stg_public_user_domains') }} ud
    join {{ ref('stg_public_domain') }} d on ud.domain_id = d.id
    group by ud.user_id
),

categories as (
    select
        uc.user_id,
        string_agg(c.name, ', ') as categories_list
    from {{ ref('stg_public_user_categories') }} uc
    join {{ ref('stg_public_category') }} c on uc.category_id = c.id
    group by uc.user_id
),

joined as (
    select
        u.*,
        coalesce(ts.tech_stacks_list, '') as tech_stacks,
        coalesce(d.domains_list, '') as domains,
        coalesce(c.categories_list, '') as categories
    from users u
    left join tech_stacks ts on u.id = ts.user_id
    left join domains d on u.id = d.user_id
    left join categories c on u.id = c.user_id
),

final as (
    select
        *,
        -- Context generation for embeddings
        {{ generate_user_context([
            ('Name', 'name'),
            ('Job Title', 'job_title'),
            ('Bio', 'bio'),
            ('Tech Stacks', 'tech_stacks'),
            ('Domains', 'domains'),
            ('Categories', 'categories')
        ]) }} 
        as context
    from joined
)

select * from final
