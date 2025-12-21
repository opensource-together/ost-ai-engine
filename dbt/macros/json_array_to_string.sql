{% macro json_array_to_string(column_name, separator=', ', normalize=true) %}
    {#
        Converts a JSONB array to a comma-separated string.
        
        Args:
            column_name: the JSONB column containing an array
            separator: delimiter between values (default: ', ')
            normalize: if true, applies lowercase + trim + dedup (default: true)
            
        Examples:
            - ["Python", "JavaScript"] → "python, javascript" (with normalize)
            - ["Python", "PYTHON"] → "python" (deduped)
            - {"key": "val"} → "" (not an array, returns empty)
    #}
    (
        select 
            coalesce(
                string_agg(
                    {% if normalize %}distinct lower(trim(value)){% else %}value{% endif %},
                    '{{ separator }}'
                    {% if normalize %}order by lower(trim(value)){% endif %}
                ),
                ''
            )
        from jsonb_array_elements_text(
            case 
                when {{ column_name }} is null then '[]'::jsonb
                when jsonb_typeof({{ column_name }}) = 'array' then {{ column_name }}
                when jsonb_typeof({{ column_name }}) = 'object' then 
                    -- Handle {lang: bytes} format from languages API
                    (select jsonb_agg(key) from jsonb_each({{ column_name }}))
                else '[]'::jsonb
            end
        )
    )
{% endmacro %}
