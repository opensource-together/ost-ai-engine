-- Source: public.Category
-- Purpose: Select ID and Name for embedding
{{ config(
    materialized='table',
    schema='ml',
    alias='int_category_embedding'
) }}

select
    id::uuid as id,
    name,
    'Category : ' || name as context
from {{ source('public', 'Category') }}
