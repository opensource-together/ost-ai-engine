-- Ensure no duplicate (user_id, project_id) pairs in recommendations
SELECT
    user_id,
    project_id,
    COUNT(*) AS cnt
FROM {{ ref('match_user_recommendation') }}
GROUP BY user_id, project_id
HAVING COUNT(*) > 1
