{{
    config(
        materialized='incremental',
        unique_key='full_name',
        alias='github_PROJECT'
    )
}}

-- This model loads raw GitHub repository data from the Go scraper into github_PROJECT table
-- It handles the INSERT/UPDATE logic that was previously in Python

WITH raw_repositories AS (
    -- Read from the raw table created by dbt
    SELECT 
        full_name,
        name,
        owner,
        description,
        fork,
        language,
        stargazers_count,
        watchers_count,
        forks_count,
        open_issues_count,
        topics,
        archived,
        disabled,
        created_at,
        updated_at,
        pushed_at,
        homepage,
        license,
        languages_map,
        readme,
        raw,
        last_ingested_at
    FROM {{ ref('raw_github_repositories') }}
    WHERE full_name IS NOT NULL
),

existing_repositories AS (
    SELECT 
        full_name,
        last_ingested_at
    FROM {{ this }}
    {% if is_incremental() %}
        WHERE last_ingested_at > (SELECT COALESCE(MAX(last_ingested_at), '1970-01-01'::timestamp) FROM {{ this }})
    {% endif %}
)

SELECT 
    r.full_name,
    r.name,
    r.owner,
    r.description,
    r.fork,
    r.language,
    r.stargazers_count,
    r.watchers_count,
    r.forks_count,
    r.open_issues_count,
    r.topics,
    r.archived,
    r.disabled,
    r.created_at,
    r.updated_at,
    r.pushed_at,
    r.homepage,
    r.license,
    r.languages_map,
    r.readme,
    r.raw,
    r.last_ingested_at
FROM raw_repositories r
LEFT JOIN existing_repositories e ON r.full_name = e.full_name
WHERE e.full_name IS NULL  -- Only insert new or updated records
