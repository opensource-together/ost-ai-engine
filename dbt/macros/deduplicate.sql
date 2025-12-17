{% macro deduplicate(cte_name, partition_by, order_by) %}
    {# 
        Selects the first row per group based on the order.
        Usage: 
        with source as (...),
        cleaned as (...)
        {{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
    #}
    select *
    from (
        select
            *,
            row_number() over (partition by {{ partition_by }} order by {{ order_by }}) as rn
        from {{ cte_name }}
    ) t
    where rn = 1
{% endmacro %}
