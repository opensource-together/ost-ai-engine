select
    id as user_id,
    name,
    bio,
    "jobTitle" as job_title,
    experiences,
    "createdAt" as created_at
from {{ source('public', 'user') }}
