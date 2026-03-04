WITH source AS (
    SELECT * FROM {{ ref('int_project_enriched') }}
),

final AS (
    SELECT
        *,
        -- Context generation
        {{ build_project_context([
            ('Title', 'name'),
            ('Description', 'description'),
            ('Topics', jsonb_to_list('fetched_topics')),
            ('Tech stacks', jsonb_to_list('fetched_languages')),
            ('Readme', clean_text('readme_content'))
        ]) }}
            AS context
    FROM source
)

SELECT
    id,
    name,
    description,
    url,
    stars,
    forks,
    open_issues_count,
    pushed_at,
    created_at,
    updated_at,
    -- Keep metadata for filtering, but remove blobs (readme, full lists) to save space
    language_confidence,
    primary_language AS language,
    context
FROM final
