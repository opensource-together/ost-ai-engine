
with source as (
    select * from {{ source('public', 'Domain') }}
),

renamed as (
    select
        id,
        name,
        "createdAt" as created_at
    from source
)

select * from renamed
