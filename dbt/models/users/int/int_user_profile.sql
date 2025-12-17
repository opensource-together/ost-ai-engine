
{{ config(
    materialized='table',
    schema='ml',
    alias='int_user_profile'
) }}

select
    id as "id",
    context as "context"
from {{ ref('pvt_user_profile') }}
where context is not null
