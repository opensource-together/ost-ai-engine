-- Verify all score components are within expected [0, 1] range
select
    user_id,
    project_id,
    similarity_score,
    freshness_score,
    popularity_score,
    final_score
from {{ ref('match_user_recommendation') }}
where
    similarity_score < 0 or similarity_score > 1
    or freshness_score < 0 or freshness_score > 1
    or popularity_score < 0 or popularity_score > 1
    or final_score < 0 or final_score > 1
