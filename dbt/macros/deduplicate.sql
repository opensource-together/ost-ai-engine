{% macro deduplicate(cte_name, partition_by, order_by) %}
    {#
        Selects the first row per group based on the order.
        Returns a SELECT statement — wrap in a CTE and select explicit columns
        to exclude the internal _rn column from final output.

        Usage:
        with source as (...),
        cleaned as (...),
        deduped as (
            {{ deduplicate('cleaned', 'project_id', 'created_at desc') }}
        )
        select col1, col2 from deduped
    #}
    select *
    from (
        select
            *,
            row_number() over (partition by {{ partition_by }} order by {{ order_by }}) as _rn
        from {{ cte_name }}
    ) _deduped
    where _rn = 1
{% endmacro %}
