{{
    config(
        materialized='incremental',
        unique_key='full_name',
        alias='PROJECT'
    )
}}

-- Force dependency on github_project_table asset for proper execution order
-- This ensures github_PROJECT table is populated before transformation
-- {{ source('dagster', 'github_project_table') }}

WITH github_projects AS (
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
        last_ingested_at
    FROM {{ source('ost_prod', 'github_PROJECT') }}
    
    {% if is_incremental() %}
        WHERE last_ingested_at > (SELECT COALESCE(MAX(last_ingested_at), '1970-01-01'::timestamp) FROM {{ this }})
    {% endif %}
),

transformed_projects AS (
    SELECT 
        -- Generate consistent UUID based on full_name to ensure referential integrity
        md5(full_name)::uuid as id,
        full_name,
        name as title,
        description,
        -- Créer short_description à partir de description (premier 200 chars)
        CASE 
            WHEN length(description) > 200 
            THEN left(description, 197) || '...'
            ELSE description
        END as short_description,
        readme,
        language as primary_language,
        homepage as homepage_url,
        license,
        COALESCE(stargazers_count, 0) as stargazers_count,
        COALESCE(watchers_count, 0) as watchers_count,
        COALESCE(forks_count, 0) as forks_count,
        COALESCE(open_issues_count, 0) as open_issues_count,
        COALESCE(fork, false) as is_fork,
        COALESCE(archived, false) as is_archived,
        COALESCE(disabled, false) as is_disabled,
        -- Convert JSONB topics to TEXT[] array
        CASE 
            WHEN topics IS NOT NULL 
            THEN ARRAY(SELECT jsonb_array_elements_text(topics))
            ELSE NULL
        END as topics,
        languages_map as languages,
        created_at,
        updated_at,
        pushed_at,
        last_ingested_at,
        -- Champs non mappés (pour l'instant null)
        NULL::TEXT as image,
        NULL::TEXT as cover_images,
        NULL::UUID as author_id,
        NULL::UUID as owner_id,
        owner as owner_login
    FROM github_projects
    WHERE full_name IS NOT NULL
    AND name IS NOT NULL
    AND NOT COALESCE(archived, false)  -- Exclure les projets archivés
    AND NOT COALESCE(disabled, false)  -- Exclure les projets désactivés
)

SELECT * FROM transformed_projects
