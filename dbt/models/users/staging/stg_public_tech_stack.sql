
with source as (
    select * from {{ source('public', 'tech_stack') }}
),

renamed as (
    select
        id,
        name,
        type,
        "iconUrl" as icon_url
    from source
)

select * from renamed
