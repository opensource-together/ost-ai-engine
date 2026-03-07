WITH source AS (
    SELECT * FROM {{ source('github', 'raw_github_project') }}
),

renamed AS (
    SELECT
        id,
        (data ->> 'stargazers_count')::int AS stars,
        (data ->> 'forks_count')::int AS forks,
        (data ->> 'open_issues_count')::int AS open_issues_count,
        (data ->> 'pushed_at')::timestamp AS pushed_at,
        "createdAt" AS created_at,
        "updatedAt" AS updated_at,
        data ->> 'name' AS name,
        data ->> 'description' AS description,
        data ->> 'html_url' AS url,
        data ->> 'language' AS language
    FROM source
    WHERE
        -- Filter out projects with empty descriptions (logic from core_github__extract_top_projects)
        data ->> 'description' IS NOT null
        AND length(trim(data ->> 'description')) > 0
        -- Filter out projects with no language (optional, but good practice if we filter by language later)
        AND data ->> 'language' IS NOT null
),

deduped AS (
    {{ deduplicate('renamed', 'url', 'created_at desc') }}
)

SELECT
    id,
    name,
    description,
    url,
    stars,
    forks,
    open_issues_count,
    language,
    pushed_at,
    created_at,
    updated_at
FROM deduped
