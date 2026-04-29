-- Global recommendations must not exceed the configured cap (same LIMIT as the model).
SELECT count(*) AS violating_row_count
FROM {{ ref('match_global_recommendation') }}
HAVING count(*) > {{ var('global_reco_top_n', 20) }}
