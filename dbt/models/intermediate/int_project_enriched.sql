WITH projects AS (
    SELECT * FROM {{ ref('stg_github__project') }}
),

readmes AS (
    SELECT * FROM {{ ref('stg_github__readme') }}
),

topics AS (
    SELECT * FROM {{ ref('stg_github__topics') }}
),

languages AS (
    SELECT * FROM {{ ref('stg_github__languages') }}
),

detection AS (
    SELECT * FROM {{ ref('stg_github__detection') }}
),

joined AS (
    SELECT
        p.id,
        p.name,
        p.description,
        p.url,
        p.stars,
        p.forks,
        p.open_issues_count,
        p.pushed_at,
        p.created_at,
        p.updated_at,

        -- Enriched fields
        d.language_detected,
        d.language_confidence,
        r.content AS readme_content,
        t.topics AS fetched_topics,
        l.languages AS fetched_languages,

        -- Fallback logic (e.g. use detected language if primary is missing)
        coalesce(p.language, d.language_detected) AS primary_language

    FROM projects AS p
    LEFT JOIN detection AS d ON p.id = d.project_id
    LEFT JOIN readmes AS r ON p.id = r.project_id
    LEFT JOIN topics AS t ON p.id = t.project_id
    LEFT JOIN languages AS l ON p.id = l.project_id
)

SELECT * FROM joined
