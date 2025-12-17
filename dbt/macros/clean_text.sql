{% macro clean_text(column_name) %}
    trim(
        regexp_replace( -- Collapse multiple newlines
            regexp_replace( -- Collapse multiple spaces
                regexp_replace( -- Remove noise (headers, footers, CTAs)
                    regexp_replace( -- Remove raw URLs
                         regexp_replace( -- Remove empty artifacts
                            regexp_replace( -- Convert Markdown links to text
                                regexp_replace( -- Remove Markdown images
                                    regexp_replace( -- Remove remaining HTML tags
                                        regexp_replace( -- Convert HTML structure tags to newlines
                                            coalesce({{ column_name }}, ''),
                                            '(?i)<(br|p|div|li|tr|h\d)[^>]*>', E'\n', 'g'
                                        ),
                                        '<[^>]+>', '', 'g'
                                    ),
                                    '!\[[^\]]*\]\([^\)]+\)', '', 'g'
                                ),
                                '\[([^\]]+)\]\([^\)]+\)', '\1', 'g' -- Keep text, discard URL
                            ),
                            '\[\s*\](\([^\)]*\))?', '', 'g'
                        ),
                        'https?://\S+', '', 'g'
                    ),
                    '(?i)^\s*(➡️|download|explore more|license|contribution|click here|copyright).*', '', 'g'
                ),
                '[ \t]+', ' ', 'g'
            ),
            '\n\s*\n+', E'\n', 'g'
        )
    )
{% endmacro %}