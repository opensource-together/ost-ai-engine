{{
    config(
        materialized='incremental',
        unique_key='project_id',
        alias='embed_PROJECTS_temp',
        indexes=[
          {'columns': ['project_id'], 'type': 'btree'}
        ],
        on_schema_change='fail'
    )
}}

-- Modèle dbt pour préparer les données d'embedding de projets
-- Enrichit les projets avec leurs catégories et construit le texte pour l'embedding
-- AJOUT: Création de vecteurs hybrides avec features structurées

WITH enriched_projects AS (
    SELECT 
        p.id as project_id,
        p.description, 
        p.short_description,
        p.readme,
        p.primary_language,
        p.homepage_url,
        p.license,
        p.topics,
        p.languages,
        p.stargazers_count,
        p.forks_count,
        p.owner_login,
        p.last_ingested_at,
        -- Aggreger categories et tech stacks dans une seule requête pour éviter les doublons
        ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL) as categories,
        ARRAY_AGG(DISTINCT ts.name) FILTER (WHERE ts.name IS NOT NULL) as tech_stacks
    FROM {{ ref('github_to_project') }} p
    LEFT JOIN {{ source('ost_prod', 'PROJECT_CATEGORY') }} pc ON p.id = pc.project_id
    LEFT JOIN {{ source('ost_prod', 'CATEGORY') }} c ON pc.category_id = c.id
    LEFT JOIN {{ source('ost_prod', 'PROJECT_TECH_STACK') }} pts ON p.id = pts.project_id
    LEFT JOIN {{ source('ost_prod', 'TECH_STACK') }} ts ON pts.tech_stack_id = ts.id
    WHERE (p.description IS NOT NULL OR p.readme IS NOT NULL)
    AND NOT COALESCE(p.is_archived, false)
    AND NOT COALESCE(p.is_disabled, false)
    {% if is_incremental() %}
        AND p.last_ingested_at > (SELECT COALESCE(MAX(last_ingested_at), '1970-01-01'::timestamp) FROM {{ this }})
    {% endif %}
    GROUP BY p.id, p.description, p.short_description, p.readme, p.primary_language, 
             p.homepage_url, p.license, p.topics, p.languages, p.stargazers_count, 
             p.forks_count, p.owner_login, p.last_ingested_at
),

enriched_text AS (
    SELECT 
        project_id,
        description,
        short_description,
        readme,
        primary_language,
        homepage_url,
        license,
        topics,
        languages,
        stargazers_count,
        forks_count,
        owner_login,
        categories,
        tech_stacks,
        last_ingested_at,
        -- Construction du texte enrichi pour embedding (minuscules + nettoyage emojis/caractères spéciaux)
        -- AJOUT: Pondération des catégories pour les rendre plus importantes
        TRIM(
        regexp_replace(
        regexp_replace(
        regexp_replace(
        lower(CONCAT_WS(' ',
            CASE WHEN description IS NOT NULL THEN CONCAT('Description: ', description) END,
            CASE WHEN short_description IS NOT NULL AND short_description != description 
                 THEN CONCAT('Summary: ', short_description) END,
            CASE WHEN readme IS NOT NULL AND LENGTH(readme) < 2000 
                 THEN CONCAT('README: ', LEFT(readme, 1000)) END,
            CASE WHEN primary_language IS NOT NULL THEN CONCAT('Language: ', primary_language) END,
            CASE WHEN topics IS NOT NULL AND array_length(topics, 1) > 0 
                 THEN CONCAT('Topics: ', array_to_string(topics, ' ')) END,
            CASE WHEN license IS NOT NULL THEN CONCAT('License: ', license) END,
            CASE WHEN owner_login IS NOT NULL THEN CONCAT('Owner: ', owner_login) END,
            -- AJOUT: Répéter les catégories 3x pour les pondérer davantage
            CASE WHEN categories IS NOT NULL AND array_length(categories, 1) > 0 
                 THEN CONCAT('Categories: ', array_to_string(categories, ' '), ' ', 
                            array_to_string(categories, ' '), ' ', 
                            array_to_string(categories, ' ')) END,
            CASE WHEN tech_stacks IS NOT NULL AND array_length(tech_stacks, 1) > 0 
                 THEN CONCAT('TechStacks: ', array_to_string(tech_stacks, ' ')) END,
            CASE WHEN languages IS NOT NULL 
                 THEN CONCAT('Languages: ', array_to_string(
                     (SELECT array_agg(key ORDER BY (value::text)::int DESC) 
                      FROM jsonb_each_text(languages) LIMIT 5), ' ')) END
        )),
        '[^a-z0-9 ]', ' ', 'g'  -- retire ponctuation/symboles (ex: =, >, etc.)
        ),
        '[^ -~]', ' ', 'g'  -- retire emojis et caractères non ASCII imprimables
        ),
        '[[:space:]]+', ' ', 'g'  -- compresse espaces multiples
        )) as embedding_text,
        -- AJOUT: Features structurées pour vecteurs hybrides
        categories as structured_categories,
        tech_stacks as structured_tech_stacks,
        primary_language as structured_language,
        COALESCE(stargazers_count, 0) as structured_stars,
        COALESCE(forks_count, 0) as structured_forks
    FROM enriched_projects
)

SELECT 
    project_id,
    embedding_text,
    structured_categories,
    structured_tech_stacks,
    structured_language,
    structured_stars,
    structured_forks,
    last_ingested_at,
    NOW() as created_at
FROM enriched_text
WHERE LENGTH(TRIM(embedding_text)) > 20  -- Minimum content
ORDER BY created_at DESC
