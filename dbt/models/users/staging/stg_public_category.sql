
with source as (
    select * from {{ source('public', 'Category') }}
),

renamed as (
    select
        id,
        name,
        "createdAt" as created_at
    from source
)

select * from renamed
