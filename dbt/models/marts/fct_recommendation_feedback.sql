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

labeled AS (
    SELECT
        impression_id,
        user_id,
        project_id,
        session_key,
        impression_rank,
        impression_at,
        similarity_score,
        preference_score,
        freshness_score,
        popularity_score,
        EXISTS(
            SELECT 1
            FROM {{ ref('stg_public__recommendation_event') }} AS interaction
            WHERE
                interaction.user_id = impressions.user_id
                AND interaction.project_id = impressions.project_id
                AND interaction.event_type IN ('CLICKED', 'STARRED_AFTER_RECO')
                AND interaction.occurred_at > impressions.impression_at
                AND interaction.occurred_at
                <= impressions.impression_at + interval '7 days'
        ) AS is_positive
    FROM impressions
)

SELECT
    impression_id,
    user_id,
    project_id,
    session_key,
    impression_rank,
    impression_at,
    is_positive,
    similarity_score,
    preference_score,
    freshness_score,
    popularity_score
FROM labeled
