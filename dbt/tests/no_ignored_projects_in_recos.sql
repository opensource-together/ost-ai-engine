-- Ensure no (user_id, project_id) pair appears in recommendations
-- if the user was shown the project ≥N times in the lookback window without clicking.
SELECT
    mur.user_id,
    mur.project_id
FROM {{ ref('match_user_recommendation') }} AS mur
INNER JOIN (
    SELECT user_id, project_id, count(*) AS n_shown
    FROM {{ ref('stg_public__recommendation_event') }}
    WHERE event_type = 'shown'
      AND occurred_at >= now() - interval '{{ var("ignored_lookback_days", 30) }} days'
    GROUP BY user_id, project_id
    HAVING count(*) >= {{ var('ignored_min_shown', 3) }}
) AS shown
    ON mur.user_id = shown.user_id AND mur.project_id = shown.project_id
LEFT JOIN (
    SELECT DISTINCT user_id, project_id
    FROM {{ ref('stg_public__recommendation_event') }}
    WHERE event_type IN ('clicked', 'starred_after_reco')
      AND occurred_at >= now() - interval '{{ var("ignored_lookback_days", 30) }} days'
) AS clicked
    ON shown.user_id = clicked.user_id AND shown.project_id = clicked.project_id
WHERE clicked.project_id IS NULL
