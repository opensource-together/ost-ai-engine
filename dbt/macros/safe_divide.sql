{% macro safe_divide(numerator, denominator, fallback='null') %}
    {#
        Divides numerator by denominator, returning fallback when denominator is zero or NULL.

        Usage:
            {{ safe_divide('shared_items::float', 'total_items') }}
            -> numerator::float / nullif(denominator, 0)

            {{ safe_divide('x', 'y', fallback='0') }}
            -> coalesce(x / nullif(y, 0), 0)

        Notes:
        - Always casts numerator to float to avoid integer division truncation.
        - When fallback is 'null' (default), returns NULL on division by zero (safe for COALESCE chains).
        - When fallback is a numeric literal (e.g. '0'), wraps in COALESCE.
    #}
    {% if fallback == 'null' %}
        ({{ numerator }})::float / nullif({{ denominator }}, 0)
    {% else %}
        coalesce(({{ numerator }})::float / nullif({{ denominator }}, 0), {{ fallback }})
    {% endif %}
{% endmacro %}
