{{
  config(
    materialized='table',
    tags=['test', 'fixtures']
  )
}}

-- Test projects for integration tests
-- This model creates a minimal set of test projects with different technologies

SELECT 
  '123e4567-e89b-12d3-a456-426614174003'::uuid as id,
  'Python ML Project' as title,
  'Machine learning project in Python with scikit-learn and pandas' as description,
  'Python' as primary_language,
  'Data Science' as category,
  1500 as stargazers_count,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174004'::uuid as id,
  'JavaScript Web App' as title,
  'Modern web application built with React and Node.js' as description,
  'JavaScript' as primary_language,
  'Web Development' as category,
  800 as stargazers_count,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174005'::uuid as id,
  'Go Microservice' as title,
  'High-performance microservice built with Go and gRPC' as description,
  'Go' as primary_language,
  'Backend Development' as category,
  1200 as stargazers_count,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174006'::uuid as id,
  'Data Science Tool' as title,
  'Data analysis and visualization tool with Jupyter notebooks' as description,
  'Python' as primary_language,
  'Data Science' as category,
  2000 as stargazers_count,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174007'::uuid as id,
  'React Component Library' as title,
  'Reusable React components with TypeScript and Storybook' as description,
  'TypeScript' as primary_language,
  'Web Development' as category,
  950 as stargazers_count,
  NOW() as created_at
