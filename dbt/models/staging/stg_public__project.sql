WITH projects AS (
    SELECT * FROM {{ source('public', 'Project') }}
),

categories AS (
    SELECT
        pc."projectId",
        string_agg(c.name, ', ') AS categories_list
    FROM {{ source('public', 'project_category') }} AS pc
    INNER JOIN {{ source('public', 'Category') }} AS c ON pc."categoryId" = c.id
    GROUP BY pc."projectId"
),

domains AS (
    SELECT
        pd."projectId",
        string_agg(d.name, ', ') AS domains_list
    FROM {{ source('public', 'project_domain') }} AS pd
    INNER JOIN {{ source('public', 'Domain') }} AS d ON pd."domainId" = d.id
    GROUP BY pd."projectId"
),

tech_stacks AS (
    SELECT
        pts."projectId",
        string_agg(ts.name, ', ') AS tech_stack_list
    FROM {{ source('public', 'project_tech_stack') }} AS pts
    INNER JOIN {{ source('public', 'tech_stack') }} AS ts ON pts."techStackId" = ts.id
    GROUP BY pts."projectId"
),

readmes AS (
    SELECT
        project_id,
        content
    FROM {{ ref('stg_github__readme') }}
)

SELECT
    p.id,
    p.title,
    p.description,
    p."repoUrl",
    p."updatedAt",
    coalesce(c.categories_list, '') AS categories,
    coalesce(d.domains_list, '') AS domains,
    coalesce(t.tech_stack_list, '') AS tech_stack,
    coalesce(r.content, '') AS readme
FROM projects AS p
LEFT JOIN categories AS c ON p.id = c."projectId"
LEFT JOIN domains AS d ON p.id = d."projectId"
LEFT JOIN tech_stacks AS t ON p.id = t."projectId"
LEFT JOIN readmes AS r ON p.id::uuid = r.project_id
WHERE p.published = true OR p.trending = true
