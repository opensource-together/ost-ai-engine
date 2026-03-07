{% macro clamp(expr, min_val=0, max_val=1.0) %}
    {#
        Clamps a numeric expression between min_val and max_val.

        Usage:
            {{ clamp('some_score_expr') }}               -> greatest(0, least(1.0, some_score_expr))
            {{ clamp('expr', min_val=0, max_val=100) }}  -> greatest(0, least(100, expr))

        This macro ensures score columns (similarity, freshness, popularity, etc.)
        stay within valid bounds even when upstream data is unexpected.
    #}
    greatest({{ min_val }}, least({{ max_val }}, {{ expr }}))
{% endmacro %}
