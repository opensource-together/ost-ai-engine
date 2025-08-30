{{
  config(
    materialized='table',
    tags=['test', 'fixtures']
  )
}}

-- Test similarities for integration tests
-- This model creates realistic similarity scores between test users and projects

WITH test_users AS (
  SELECT * FROM {{ ref('test_users') }}
),
test_projects AS (
  SELECT * FROM {{ ref('test_projects') }}
),
similarity_calculations AS (
  SELECT 
    u.id as user_id,
    p.id as project_id,
    -- Realistic similarity scores based on language and category matches
    CASE 
      WHEN u.primary_language = p.primary_language THEN 0.85 + (random() * 0.10)
      WHEN u.category = p.category THEN 0.70 + (random() * 0.15)
      ELSE 0.50 + (random() * 0.20)
    END as similarity_score,
    
    -- Semantic similarity (based on language match)
    CASE 
      WHEN u.primary_language = p.primary_language THEN 0.80 + (random() * 0.15)
      ELSE 0.60 + (random() * 0.20)
    END as semantic_similarity,
    
    -- Category similarity
    CASE 
      WHEN u.category = p.category THEN 0.90 + (random() * 0.08)
      ELSE 0.65 + (random() * 0.20)
    END as category_similarity,
    
    -- Language similarity
    CASE 
      WHEN u.primary_language = p.primary_language THEN 0.85 + (random() * 0.12)
      ELSE 0.55 + (random() * 0.25)
    END as language_similarity,
    
    -- Popularity similarity (normalized stargazers)
    (p.stargazers_count / 2000.0) as popularity_similarity,
    
    NOW() as created_at

  FROM test_users u
  CROSS JOIN test_projects p
),
ranked_similarities AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY user_id 
      ORDER BY similarity_score DESC
    ) as rn
  FROM similarity_calculations
)

-- Ensure we have exactly 5 recommendations per user (RECOMMENDATION_TOP_N)
SELECT 
  user_id,
  project_id,
  similarity_score,
  semantic_similarity,
  category_similarity,
  language_similarity,
  popularity_similarity,
  created_at
FROM ranked_similarities 
WHERE rn <= 5
