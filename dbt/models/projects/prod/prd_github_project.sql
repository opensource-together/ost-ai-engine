with pivot as (
    select * from {{ ref('pvt_github_project') }}
),

embeddings as (
    select * from {{ source('ml', 'embd_github_project') }}
),

    final as (
    select
        p.id::uuid,
        p.name as title,
        p.description,
        p.url as "repoUrl",
        'GITHUB' as provider, -- Enum value
        p.url as "githubUrl",
        null as "gitlabUrl",
        null as "twitterUrl",
        null as "linkedinUrl",
        null as "discordUrl",
        null as "websiteUrl",
        false as published, -- Default
        false as trending, -- Default
        
        -- Additional metadata not in Prisma schema directly but useful?
        -- For now, we stick to the schema.
        -- p.stars, p.forks, p.language, p.topics... 
        -- These might belong in a separate table or JSON column if not in Project model.
        -- But wait, Project model has relations.
        -- Let's keep it simple and map what fits.
        
        p.created_at as "createdAt",
        p.updated_at as "updatedAt"
        
    from pivot p
    -- Embeddings are in a separate table in Prisma (ProjectEmbedding), so we don't join them here for the main Project table.
    -- If we want to populate ProjectEmbedding, that would be a separate model or process.
)

select * from final
