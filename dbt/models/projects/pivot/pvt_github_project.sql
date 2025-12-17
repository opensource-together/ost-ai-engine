
with source as (
    select * from {{ ref('int_github_project') }}
),

final as (
    select
        *,
        -- Context generation
        {{ generate_project_context([
            ('Title', 'name'),
            ('Description', 'description'),
            ('Topics', json_array_to_string('fetched_topics')),
            ('Tech stacks', json_array_to_string('fetched_languages')),
            ('Readme', clean_llm_context('readme_content'))
        ]) }} 
        as context
    from source
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
