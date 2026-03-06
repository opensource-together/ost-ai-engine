WITH source AS (
    SELECT * FROM {{ source('github', 'raw_github_topics') }}
),

cleaned AS (
    SELECT
        s.id,
        s.project_id::uuid AS project_id,
        s.repo_url,
        s.topics,
        s.created_at
    FROM source AS s
    INNER JOIN {{ ref('stg_github__project') }} AS p ON s.project_id::uuid = p.id
),

deduped AS (
    {{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
)

SELECT
    id,
    project_id,
    repo_url,
    topics,
    created_at
FROM deduped
