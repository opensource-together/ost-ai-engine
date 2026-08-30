WITH projects AS (
    SELECT
        id,
        trending,
        published,
        "updatedAt"
    FROM {{ source('public', 'Project') }}
),

metadata AS (
    SELECT
        id,
        stars
    FROM {{ ref('fct_github_project') }}
),

final AS (
    SELECT
        p.id AS project_id,
        m.stars,
        p."updatedAt" AS last_synced_at
    FROM projects AS p
    INNER JOIN metadata AS m ON p.id::uuid = m.id
    WHERE p.trending = true OR p.published = true
    ORDER BY p."updatedAt" DESC, m.stars DESC
    LIMIT {{ var('global_reco_top_n', 20) }}
)

SELECT * FROM final
