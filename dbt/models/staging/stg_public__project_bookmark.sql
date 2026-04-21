SELECT
    "userId"    AS user_id,
    "projectId" AS project_id,
    "createdAt" AS created_at
FROM {{ source('public', 'project_bookmark') }}
