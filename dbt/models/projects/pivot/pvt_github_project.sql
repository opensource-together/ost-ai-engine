with source as (
    select * from {{ ref('int_github_project') }}
),

final as (
    select
        *,
        -- Context generation
        {{ build_project_context([
            ('Title', 'name'),
            ('Description', 'description'),
            ('Topics', jsonb_to_list('fetched_topics')),
            ('Tech stacks', jsonb_to_list('fetched_languages')),
            ('Readme', clean_text('readme_content'))
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
    -- Keep metadata for filtering, but remove blobs (readme, full lists) to save space
    language_confidence,
    primary_language as language,
    context
from final
