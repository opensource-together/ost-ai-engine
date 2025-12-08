with pivot as (
    select * from {{ ref('pivot_github_project') }}
),

embeddings as (
    select * from {{ source('ost', 'embd_github_project') }}
),

final as (
    select
        p.id,
        p.name,
        p.description,
        p.url,
        p.stars,
        p.forks,
        p.language,
        p."enrichedData",
        e."embeddingVector"
    from pivot p
    left join embeddings e on p.id = e."projectId"
)

select * from final
