{% macro clean_llm_context(column_name) %}
    trim(
        regexp_replace( -- 6. Collapse multiple newlines/spaces into single space (LLM reads stream)
            regexp_replace( -- 5. Collapse repeated punctuation (!!!! -> !)
                regexp_replace( -- 4. Remove Markdown Images (![alt](url)) but KEEP Links ([text](url))
                     regexp_replace( -- 3. Remove base64/long strings (simple heuristic: >50 chars no space)
                        regexp_replace( -- 2. Convert HTML tags to space (avoid word merging)
                            coalesce({{ column_name }}, ''),
                            '<[^>]+>', ' ', 'g'
                        ),
                        '\S{100,}', '', 'g' -- Remove very long non-spaced strings (likely base64 or minified code)
                    ),
                    '!\[[^\]]*\]\([^\)]+\)', '', 'g' -- Drop images
                ),
                '([!?.])\1+', '\1', 'g' -- Collapse '!!!!' or '....'
            ),
            '\s+', ' ', 'g' -- Normalize whitespace to single space
        )
    )
{% endmacro %}
