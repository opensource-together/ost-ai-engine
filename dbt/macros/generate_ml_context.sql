{% macro generate_ml_context(title, description, categories, domains, tech_stack, readme) %}
    concat_ws('\n',
        'Title: ' || coalesce({{ title }}, ''),
        'Description: ' || coalesce({{ description }}, ''),
        'Categories: ' || coalesce({{ categories }}, ''),
        'Domains: ' || coalesce({{ domains }}, ''),
        'Tech Stack: ' || coalesce({{ tech_stack }}, ''),
        'README: ' || substring(coalesce({{ readme }}, ''), 1, 3000)
    )
{% endmacro %}
