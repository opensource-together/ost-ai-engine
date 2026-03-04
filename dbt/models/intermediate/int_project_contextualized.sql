WITH public_projects AS (
    SELECT * FROM {{ ref('stg_public__project') }}
),

contextualized AS (
    SELECT
        p.id,
        {{ build_project_context([
            ('Title', 'p.title'),
            ('Description', 'p.description'),
            ('Categories', 'p.categories'),
            ('Domains', 'p.domains'),
            ('Tech Stack', 'p.tech_stack'),
            ('Readme', clean_text('p.readme'))
        ]) }} AS raw_context,
        now() AS created_at
    FROM public_projects AS p
    WHERE p.id IS NOT null
)

SELECT
    id,
    {{ clean_text('raw_context') }} AS context,
    created_at
FROM contextualized
WHERE
    raw_context IS NOT null
    AND length(trim(raw_context)) > 10
