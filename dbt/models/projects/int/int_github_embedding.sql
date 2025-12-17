
{{ config(
    materialized='table',
    schema='github',
    alias='int_github_embedding'
) }}

select
    id as "id",
    context as "context"
from {{ ref('pvt_github_project') }}
where context is not null
