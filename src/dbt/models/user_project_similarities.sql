{{
  config(
    materialized='table',
    alias='user_project_similarities_temp',
    indexes=[
        {'columns': ['user_id'], 'type': 'btree'},
        {'columns': ['project_id'], 'type': 'btree'}
    ]
  )
}}

-- Temporary model for User↔Project similarity calculations preparation
-- This model prepares the data structure for similarity calculations
-- Final results are stored in USER_PROJECT_SIMILARITY table

WITH user_data AS (
  SELECT 
    u.user_id,
    u.username,
    u.embedding_vector,
    u.categories as user_categories,
    array_agg(DISTINCT ts.name) as user_tech_stacks
  FROM {{ ref('embed_USERS') }} u
  LEFT JOIN {{ source('ost_prod', 'USER_TECH_STACK') }} uts ON u.user_id = uts.user_id
  LEFT JOIN {{ source('ost_prod', 'TECH_STACK') }} ts ON uts.tech_stack_id = ts.id
  WHERE u.embedding_vector IS NOT NULL
  GROUP BY u.user_id, u.username, u.embedding_vector, u.categories
),

project_data AS (
  SELECT 
    p.project_id,
    array_agg(DISTINCT c.name) as project_categories,
    array_agg(DISTINCT ts.name) as project_tech_stacks,
    pr.primary_language,
    pr.stargazers_count,
    pr.forks_count,
    pr.title,
    pr.description
  FROM {{ ref('ml_project_embeddings') }} p
  JOIN {{ source('ost_prod', 'PROJECT') }} pr ON p.project_id = pr.id
  LEFT JOIN {{ source('ost_prod', 'PROJECT_CATEGORY') }} pc ON p.project_id = pc.project_id
  LEFT JOIN {{ source('ost_prod', 'CATEGORY') }} c ON pc.category_id = c.id
  LEFT JOIN {{ source('ost_prod', 'PROJECT_TECH_STACK') }} pts ON p.project_id = pts.project_id
  LEFT JOIN {{ source('ost_prod', 'TECH_STACK') }} ts ON pts.tech_stack_id = ts.id
  GROUP BY p.project_id, pr.primary_language, pr.stargazers_count, pr.forks_count, pr.title, pr.description
)

SELECT 
  u.user_id,
  p.project_id,
  u.username,
  p.title as project_title,
  p.description as project_description,
  u.embedding_vector as user_embedding,
  u.user_categories,
  p.project_categories,
  u.user_tech_stacks,
  p.project_tech_stacks,
  p.stargazers_count,
  p.forks_count,
  p.primary_language,
  NOW() as created_at
FROM user_data u
CROSS JOIN project_data p
