with staging as (
    select * from {{ ref('stg_github_project') }}
),

intermediate as (
    select * from {{ source('ost', 'int_github_project') }}
),

joined as (
    select
        s.id,
        s.name,
        s.description,
        s.url,
        s.stars,
        s.forks,
        s.language,
        s.topics as stg_topics,
        i."enrichedData",
        -- Combine topics if needed, or just keep enrichedData
        -- For context generation, we need description, readme (in enrichedData), topics.
        s.created_at,
        s.updated_at
    from staging s
    left join intermediate i on s.id = i."projectId"
)

select * from joined
