WITH projects AS (
    SELECT * FROM {{ source('public', 'Project') }}
),

classifications AS (
    SELECT * FROM {{ source('match', 'project_classification') }}
),

categories AS (
    SELECT * FROM {{ source('public', 'Category') }}
),

domains AS (
    SELECT * FROM {{ source('public', 'Domain') }}
),

original_context AS (
    SELECT
        id,
        context
    FROM {{ ref('int_project_contextualized') }}
),

enriched AS (
    SELECT
        p.id AS project_id,
        concat(
            coalesce(oc.context, ''),
            ' | Category: ', coalesce(c.name, 'Uncategorized'),
            ' | Domain: ', coalesce(d.name, 'General')
        ) AS rich_context_string
    FROM projects AS p
    LEFT JOIN classifications AS cl ON p.id = cl."projectId"
    LEFT JOIN categories AS c ON cl."categoryId" = c.id
    LEFT JOIN domains AS d ON cl."domainId" = d.id
    LEFT JOIN original_context AS oc ON p.id::uuid = oc.id
    WHERE p.published = true OR p.trending = true
)

SELECT
    project_id,
    rich_context_string
FROM enriched
