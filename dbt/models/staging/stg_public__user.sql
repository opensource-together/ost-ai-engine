SELECT
    id AS user_id,
    name,
    bio,
    "jobTitle" AS job_title,
    experiences,
    "createdAt" AS created_at
FROM {{ source('public', 'user') }}
