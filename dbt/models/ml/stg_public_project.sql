
with source as (
    select * from {{ ref('raw_public_project') }}
)

select
    id,
    -- Clean the context to remove noise (e.g. empty lines, bad chars)
    -- Using the existing clean macro or standard regex if macro not fit.
    -- Assuming clean_llm_context is available (used in projects/pvt).
    {{ clean_llm_context('context') }} as context,
    created_at
from source
where context is not null
and length(trim(context)) > 10
