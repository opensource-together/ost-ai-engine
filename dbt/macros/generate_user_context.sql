{% macro generate_user_context(fields) %}
    {# 
        Generates a concatenated context string from a list of (label, column) tuples.
        Args:
            fields: list of tuples [('Label', 'column_name'), ...]
    #}
    {%- set chunks = [] -%}
    {%- for label, column in fields -%}
        {%- set chunk -%}
        '{{ label }}: ' || coalesce({{ column }}, '') || E'\n'
        {%- endset -%}
        {%- do chunks.append(chunk) -%}
    {%- endfor -%}
    
    {{ chunks | join(" || ") }}
{% endmacro %}
