{#- Label lookahead and rolling training window, in days. The maturity filter
    below must use the same lookahead as the attribution join. -#}
{% set label_window_days = 7 %}
{% set rolling_window_days = 365 %}

-- Every personalized impression ever recorded: attribution must see recent
-- impressions even when they are still too immature to be emitted, otherwise
-- a fresh click would leak onto an older impression of the same project.
WITH impressions AS (
    SELECT
        id AS impression_id,
        user_id,
        project_id,
        rank AS impression_rank,
        occurred_at AS impression_at,
        COALESCE(
            NULLIF(context ->> 'sessionId', ''),
            user_id::text || ':' || TO_CHAR(occurred_at, 'YYYY-MM-DD')
        ) AS session_key,
        -- Feature snapshots as they were shown, not the current recommendation
        -- score. This avoids training on labels leaking hindsight-updated
        -- scores. Legacy events without a snapshot yield NULL here: they stay
        -- metrics rows below but are excluded from ranker training.
        {{ safe_double("context ->> 'similarityScore'") }} AS similarity_score,
        {{ safe_double("context ->> 'preferenceScore'") }} AS preference_score,
        {{ safe_double("context ->> 'freshnessScore'") }} AS freshness_score,
        {{ safe_double("context ->> 'popularityScore'") }} AS popularity_score
    FROM {{ ref('stg_public__recommendation_event') }}
    WHERE
        event_type = 'SHOWN'
        AND source = 'PERSONALIZED'
),

-- Only personalized interactions count: a click coming from trending,
-- similar or semantic search is not credit for a for-you impression.
interactions AS (
    SELECT
        user_id,
        project_id,
        occurred_at
    FROM {{ ref('stg_public__recommendation_event') }}
    WHERE
        event_type IN ('CLICKED', 'STARRED_AFTER_RECO')
        AND source = 'PERSONALIZED'
),

-- Last-touch attribution: each interaction credits exactly one impression,
-- the nearest one preceding it inside the label window.
credited AS (
    SELECT DISTINCT nearest.impression_id
    FROM interactions AS i
    CROSS JOIN LATERAL (
        SELECT imp.impression_id
        FROM impressions AS imp
        WHERE
            imp.user_id = i.user_id
            AND imp.project_id = i.project_id
            AND i.occurred_at > imp.impression_at
            AND i.occurred_at
            <= imp.impression_at + interval '{{ label_window_days }} days'
        ORDER BY imp.impression_at DESC, imp.impression_id ASC
        LIMIT 1
    ) AS nearest
)

SELECT
    imp.impression_id,
    imp.user_id,
    imp.project_id,
    imp.session_key,
    imp.impression_rank,
    imp.impression_at,
    imp.similarity_score,
    imp.preference_score,
    imp.freshness_score,
    imp.popularity_score,
    c.impression_id IS NOT null AS is_positive
FROM impressions AS imp
LEFT JOIN credited AS c ON imp.impression_id = c.impression_id
WHERE
    -- Maturity: keep only impressions whose full label window has elapsed, so
    -- no row is labeled negative while its click or star can still arrive.
    imp.impression_at
    <= {{ feedback_as_of() }} - interval '{{ label_window_days }} days'
    -- Rolling window: bounds the fact's size and keeps training recent.
    AND imp.impression_at
    >= {{ feedback_as_of() }} - interval '{{ rolling_window_days }} days'
