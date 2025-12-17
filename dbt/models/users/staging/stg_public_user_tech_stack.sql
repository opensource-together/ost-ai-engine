
with source as (
    select * from {{ source('public', 'user_tech_stack') }}
),

renamed as (
    select
        "userId" as user_id,
        "techStackId" as tech_stack_id,
        "createdAt" as created_at
    from source
)

select * from renamed
