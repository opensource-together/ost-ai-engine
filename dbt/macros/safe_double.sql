{% macro safe_double(expr) %}
    {#
        Safely casts a text expression to double precision, returning NULL
        instead of erroring when the value is missing or not numeric.

        Usage:
            {{ safe_double("context ->> 'similarityScore'") }}
            -> numeric text becomes a double, anything else (including NULL) is NULL

        Intended for JSON/text snapshot fields captured at event time (e.g.
        recommendation_event.context), where legacy or malformed values must
        not fail the query.
    #}
    CASE
        WHEN ({{ expr }}) ~ '^-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN ({{ expr }})::double precision
        ELSE null
    END
{% endmacro %}
