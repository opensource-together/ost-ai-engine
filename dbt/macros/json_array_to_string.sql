{% macro json_array_to_string(column_name, separator=', ') %}
    (select string_agg(value, '{{ separator }}') from jsonb_array_elements_text({{ column_name }}))
{% endmacro %}
