WITH user_base AS (
    SELECT * FROM {{ ref('stg_public__user') }}
),

tech_stacks AS (
    SELECT
        uts."userId" AS user_id,
        string_agg(ts.name, ', ') AS tech_stack_list
    FROM {{ source('public', 'user_tech_stack') }} AS uts
    INNER JOIN {{ source('public', 'tech_stack') }} AS ts ON uts."techStackId" = ts.id
    GROUP BY uts."userId"
),

domains AS (
    SELECT
        ud."userId" AS user_id,
        string_agg(d.name, ', ') AS domain_list
    FROM {{ source('public', 'user_domain') }} AS ud
    INNER JOIN {{ source('public', 'Domain') }} AS d ON ud."domainId" = d.id
    GROUP BY ud."userId"
),

categories AS (
    SELECT
        uc."userId" AS user_id,
        string_agg(c.name, ', ') AS category_list
    FROM {{ source('public', 'user_categories') }} AS uc
    INNER JOIN {{ source('public', 'Category') }} AS c ON uc."categoryId" = c.id
    GROUP BY uc."userId"
)

SELECT
    u.user_id,
    u.name,
    u.bio,
    u.job_title,
    u.experiences,
    coalesce(t.tech_stack_list, '') AS tech_stacks,
    coalesce(d.domain_list, '') AS domains,
    coalesce(c.category_list, '') AS categories
FROM user_base AS u
LEFT JOIN tech_stacks AS t ON u.user_id = t.user_id
LEFT JOIN domains AS d ON u.user_id = d.user_id
LEFT JOIN categories AS c ON u.user_id = c.user_id
