{{
  config(
    materialized='table',
    tags=['test', 'fixtures']
  )
}}

-- Test users for integration tests
-- This model creates a minimal set of test users with different profiles

SELECT 
  '123e4567-e89b-12d3-a456-426614174000'::uuid as id,
  'test_user_1' as username,
  'user1@test.com' as email,
  'Python' as primary_language,
  'Data Science' as category,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174001'::uuid as id,
  'test_user_2' as username,
  'user2@test.com' as email,
  'JavaScript' as primary_language,
  'Web Development' as category,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174002'::uuid as id,
  'test_user_3' as username,
  'user3@test.com' as email,
  'Go' as primary_language,
  'Backend Development' as category,
  NOW() as created_at
