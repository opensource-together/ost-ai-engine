{% macro generate_project_context(fields) %}
    {# 
        Generates a concatenated context string for Projects.
        Args:
            fields: list of tuples [('Label', 'column_name'), ...]
            
        Special handling:
        If label is 'Tech stacks', we format it as 'Tech stacks : <value>'.
    #}
    {%- set chunks = [] -%}
    {%- for label, column in fields -%}
        {%- set chunk -%}
        E'## {{ label }}\n' || coalesce({{ column }}, '') || E'\n\n'
        {%- endset -%}
        {%- do chunks.append(chunk) -%}
    {%- endfor -%}
    
    {{ chunks | join(" || ") }}
{% endmacro %}
