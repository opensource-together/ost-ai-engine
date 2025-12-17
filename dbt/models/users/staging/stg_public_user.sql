
with source as (
    select * from {{ source('public', 'user') }}
),

renamed as (
    select
        id,
        name,
        email,
        bio,
        "jobTitle" as job_title,
        experiences,
        "githubUsername" as github_username,
        "websiteUrl" as website_url,
        "createdAt" as created_at
    from source
)

select * from renamed
