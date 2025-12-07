with staging as (
    select * from {{ ref('stg_github_project') }}
),

intermediate as (
    select * from {{ source('ost', 'int_github_project') }}
),

embeddings as (
    select * from {{ source('ost', 'embd_github_project') }}
),

final as (
    select
        s.id,
        s.name,
        s.description,
        s.url,
        s.stars,
        s.forks,
        s.language,
        i."enrichedData",
        e."embeddingVector"
    from staging s
    left join intermediate i on s.id = i."projectId"
    left join embeddings e on s.id = e."projectId"
)

select * from final
