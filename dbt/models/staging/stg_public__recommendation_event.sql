SELECT
    id,
    "userId"      AS user_id,
    "projectId"   AS project_id,
    "eventType"   AS event_type,
    source,
    rank,
    context,
    "occurredAt"  AS occurred_at
FROM {{ source('public', 'recommendation_event') }}
