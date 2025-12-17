
with source as (
    select * from {{ source('public', 'user_domain') }}
),

renamed as (
    select
        "userId" as user_id,
        "domainId" as domain_id,
        "createdAt" as created_at
    from source
)

select * from renamed
