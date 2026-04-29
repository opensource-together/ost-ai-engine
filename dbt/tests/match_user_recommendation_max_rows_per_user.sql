-- Each user must have at most reco_top_n recommendations (row_number cap in the model).
SELECT
    user_id,
    count(*) AS cnt
FROM {{ ref('match_user_recommendation') }}
GROUP BY user_id
HAVING count(*) > {{ var('reco_top_n', 30) }}
