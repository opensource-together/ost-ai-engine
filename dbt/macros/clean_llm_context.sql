{% macro clean_llm_context(column_name, max_length=8000) %}
    {#
        Cleans text for optimal LLM context understanding.
        
        Transformations (in order):
        1. Remove code blocks (```...```) - noise for understanding project purpose
        2. Remove HTML tags → space
        3. Extract link text from markdown links [text](url) → text
        4. Remove markdown images ![alt](url)
        5. Remove bare URLs (http/https)
        6. Remove very long strings (base64, minified code)
        7. Remove emojis and special unicode
        8. Collapse repeated punctuation
        9. Normalize whitespace
        10. Truncate to max_length
    #}
    left(
        trim(
            regexp_replace( -- 9. Normalize all whitespace to single space
                regexp_replace( -- 8. Collapse repeated punctuation (!!!! -> !, .... -> .)
                    regexp_replace( -- 7. Remove emojis and most special unicode (keep basic latin + accents)
                        regexp_replace( -- 6. Remove very long non-spaced strings (base64, hashes, minified)
                            regexp_replace( -- 5. Remove bare URLs
                                regexp_replace( -- 4. Remove markdown images ![alt](url)
                                    regexp_replace( -- 3. Extract text from markdown links [text](url) -> text
                                        regexp_replace( -- 2. Convert HTML tags to space
                                            regexp_replace( -- 1. Remove code blocks (```lang ... ```)
                                                coalesce({{ column_name }}, ''),
                                                '```[^`]*```', ' ', 'g'
                                            ),
                                            '<[^>]+>', ' ', 'g'
                                        ),
                                        '\[([^\]]+)\]\([^\)]+\)', '\1', 'g'  -- Keep link text, drop URL
                                    ),
                                    '!\[[^\]]*\]\([^\)]+\)', '', 'g'  -- Remove images entirely
                                ),
                                'https?://[^\s\)>\]]+', '', 'g'  -- Remove bare URLs
                            ),
                            '\S{80,}', '', 'g'  -- Remove long unspaced strings
                        ),
                        '[^\x20-\x7E\xA0-\xFF\n]', '', 'g'  -- Keep ASCII + Latin-1, remove emojis
                    ),
                    '([!?.,;:])\\1+', '\\1', 'g'  -- Collapse repeated punctuation
                ),
                '\s+', ' ', 'g'
            )
        ),
        {{ max_length }}  -- Truncate for embedding models
    )
{% endmacro %}
