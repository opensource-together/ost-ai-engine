{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['user_id'], 'type': 'btree'},
      {'columns': ['username'], 'type': 'btree'}
    ]
  )
}}

-- This model creates embed_USERS table for user embedding preparation
-- Similar to embed_PROJECTS but for users

WITH user_categories AS (
  SELECT 
    u.id as user_id,
    u.username,
    u.email,
    u.login,
    u.bio,
    u.location,
    u.company,
    u.created_at,
    u.updated_at,
    array_agg(c.name) as categories
  FROM "USER" u
  LEFT JOIN "USER_CATEGORY" uc ON u.id = uc.user_id
  LEFT JOIN "CATEGORY" c ON uc.category_id = c.id
  GROUP BY u.id, u.username, u.email, u.login, u.bio, u.location, u.company, u.created_at, u.updated_at
)

SELECT 
  user_id,
  username,
  -- Clean and prepare text for embeddings (same pattern as projects)
  regexp_replace(
    regexp_replace(
      regexp_replace(
        lower(CONCAT_WS(' ',
          CASE WHEN username IS NOT NULL THEN CONCAT('Username: ', username) END,
          CASE WHEN bio IS NOT NULL THEN CONCAT('Bio: ', bio) END,
          CASE WHEN location IS NOT NULL THEN CONCAT('Location: ', location) END,
          CASE WHEN company IS NOT NULL THEN CONCAT('Company: ', company) END,
          CASE WHEN categories IS NOT NULL AND array_length(categories, 1) > 0
               THEN CONCAT('Categories: ', array_to_string(categories, ' ')) END
        )),
        '[^[:ascii:]]', '', 'g' -- Remove non-ASCII characters (including emojis)
      ),
      '[^a-z0-9\s]', ' ', 'g' -- Remove punctuation/symbols, keep only letters, digits, spaces
    ),
    '\s+', ' ', 'g' -- Replace multiple spaces with a single space
  ) as embedding_text,
  bio,
  categories,
  CAST(NULL AS vector(384)) as embedding_vector,  -- ✅ Explicit vector(384) type
  NOW() as last_ingested_at,
  NOW() as created_at
FROM user_categories
WHERE bio IS NOT NULL AND LENGTH(bio) > 10  -- Only users with meaningful bios
