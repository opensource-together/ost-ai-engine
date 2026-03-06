-- Verify all score components are within expected [0, 1] range
SELECT
    user_id,
    project_id,
    similarity_score,
    preference_score,
    freshness_score,
    popularity_score,
    final_score
FROM {{ ref('match_user_recommendation') }}
WHERE
    similarity_score < 0 OR similarity_score > 1
    OR preference_score < 0 OR preference_score > 1
    OR freshness_score < 0 OR freshness_score > 1
    OR popularity_score < 0 OR popularity_score > 1
    OR final_score < 0 OR final_score > 1
