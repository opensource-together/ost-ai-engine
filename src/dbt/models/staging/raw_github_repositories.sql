{{
    config(
        materialized='table',
        schema='raw',
        alias='raw_github_repositories'
    )
}}

-- This model creates the raw_github_repositories table and loads data from Go scraper
-- It handles the table creation and data insertion that was previously in Python

-- For now, we'll create an empty table structure
-- The actual data will be loaded by the Go scraper via Python
SELECT 
    CAST(NULL AS TEXT) as full_name,
    CAST(NULL AS TEXT) as name,
    CAST(NULL AS TEXT) as owner,
    CAST(NULL AS TEXT) as description,
    CAST(NULL AS BOOLEAN) as fork,
    CAST(NULL AS TEXT) as language,
    CAST(NULL AS INTEGER) as stargazers_count,
    CAST(NULL AS INTEGER) as watchers_count,
    CAST(NULL AS INTEGER) as forks_count,
    CAST(NULL AS INTEGER) as open_issues_count,
    CAST(NULL AS JSONB) as topics,
    CAST(NULL AS BOOLEAN) as archived,
    CAST(NULL AS BOOLEAN) as disabled,
    CAST(NULL AS TIMESTAMP) as created_at,
    CAST(NULL AS TIMESTAMP) as updated_at,
    CAST(NULL AS TIMESTAMP) as pushed_at,
    CAST(NULL AS TEXT) as homepage,
    CAST(NULL AS TEXT) as license,
    CAST(NULL AS JSONB) as languages_map,
    CAST(NULL AS TEXT) as readme,
    CAST(NULL AS JSONB) as raw,
    CAST(NULL AS TIMESTAMP) as last_ingested_at
WHERE FALSE  -- This ensures no rows are returned, just creates the table structure
