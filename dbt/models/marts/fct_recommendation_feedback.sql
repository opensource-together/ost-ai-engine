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
        ) AS session_key
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
    labeled.impression_id,
    labeled.user_id,
    labeled.project_id,
    labeled.session_key,
    labeled.impression_rank,
    labeled.impression_at,
    labeled.is_positive,
    recommendation.similarity_score,
    recommendation.preference_score,
    recommendation.freshness_score,
    recommendation.popularity_score
FROM labeled
LEFT JOIN {{ ref('match_user_recommendation') }} AS recommendation
    ON
        labeled.user_id = recommendation.user_id
        AND labeled.project_id = recommendation.project_id
