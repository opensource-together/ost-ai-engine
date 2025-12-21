{% macro json_array_to_string(column_name, separator=', ') %}
    (select string_agg(value, '{{ separator }}') from jsonb_array_elements_text(
        case 
            when jsonb_typeof({{ column_name }}) = 'array' then {{ column_name }}
            else '[]'::jsonb
        end
    ))
{% endmacro %}
