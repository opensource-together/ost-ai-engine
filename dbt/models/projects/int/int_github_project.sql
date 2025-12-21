with projects as (
    select * from {{ ref('stg_github_project') }}
),

readmes as (
    select * from {{ ref('stg_github_readme') }}
),

topics as (
    select * from {{ ref('stg_github_topics') }}
),

languages as (
    select * from {{ ref('stg_github_languages') }}
),

detection as (
    select * from {{ ref('stg_github_detection') }}
),

joined as (
    select
        p.id,
        p.name,
        p.description,
        p.url,
        p.stars,
        p.forks,
        p.created_at,
        p.updated_at,
        
        -- Enriched fields
        d.language_detected,
        d.language_confidence,
        r.content as readme_content,
        t.topics as fetched_topics,
        l.languages as fetched_languages,
        
        -- Fallback logic (e.g. use detected language if primary is missing)
        coalesce(p.language, d.language_detected) as primary_language
        
    from projects p
    inner join detection d on p.id = d.project_id
    left join readmes r on p.id = r.project_id
    left join topics t on p.id = t.project_id
    left join languages l on p.id = l.project_id
)

select * from joined
