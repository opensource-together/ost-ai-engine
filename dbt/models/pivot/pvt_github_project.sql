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
),

final as (
    select
        *,
        -- Context generation for embeddings
        'Title: ' || coalesce(name, 'Unknown') || E'\n' ||
        'Description: ' || coalesce(description, '') || E'\n' ||
        'Topics: ' || coalesce((
            select string_agg(value, ', ')
            from jsonb_array_elements_text(fetched_topics)
        ), '') || E'\n' ||
        'Readme: ' || {{ clean_text('readme_content') }} 
        as context
    from joined
)

select
    id,
    name,
    description,
    url,
    stars,
    forks,
    created_at,
    updated_at,
    readme_content as readme,
    fetched_topics as topics,
    fetched_languages as languages,
    language_detected,
    language_confidence,
    primary_language as language,
    context
from final
