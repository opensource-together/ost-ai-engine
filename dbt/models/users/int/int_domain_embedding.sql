-- Source: public.Domain
-- Purpose: Select ID and Name for embedding
{{ config(
    materialized='table',
    schema='ml',
    alias='int_domain_embedding'
) }}

select
    id::uuid as id,
    name,
    'Domain : ' || name as context
from {{ source('public', 'Domain') }}
