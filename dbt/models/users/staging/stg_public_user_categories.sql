
with source as (
    select * from {{ source('public', 'user_categories') }}
),

renamed as (
    select
        "userId" as user_id,
        "categoryId" as category_id,
        "createdAt" as created_at
    from source
)

select * from renamed
