
with source as (
    select * from {{ ref('raw_public_project') }}
)

select
    id,
    -- Clean the context to remove noise (e.g. empty lines, bad chars)
    {{ clean_text('context') }} as context,
    created_at
from source
where context is not null
and length(trim(context)) > 10
