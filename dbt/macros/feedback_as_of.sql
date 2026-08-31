{% macro feedback_as_of() %}
    {#
        Wall clock used by the recommendation feedback fact for its maturity
        and rolling-window filters.

        Exists as a macro so unit tests can pin it to a fixed timestamp and
        keep their fixtures deterministic:

            overrides:
              macros:
                feedback_as_of: "'2026-01-20 00:00:00'::timestamp"
    #}
    now()
{% endmacro %}
