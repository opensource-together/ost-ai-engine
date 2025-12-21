{% macro generate_project_context(fields, skip_empty=true) %}
    {# 
        Generates a structured context string optimized for LLM understanding.
        
        Args:
            fields: list of tuples [('Label', 'column_name'), ...]
            skip_empty: if true, sections with empty values are omitted
            
        Output format (Markdown-like, proven effective for LLMs):
        
        # Project Overview
        
        ## Title
        Project Name Here
        
        ## Description
        What the project does...
    #}
    {%- set chunks = [] -%}
    
    {# Add a header to establish context #}
    {%- do chunks.append("E'# Project Overview\n\n'") -%}
    
    {%- for label, column in fields -%}
        {%- if skip_empty -%}
            {# Only include section if value is not null/empty #}
            {%- set chunk -%}
            case 
                when length(trim(coalesce({{ column }}::text, ''))) > 0 
                then E'## {{ label }}\n' || trim({{ column }}::text) || E'\n\n'
                else ''
            end
            {%- endset -%}
        {%- else -%}
            {%- set chunk -%}
            E'## {{ label }}\n' || coalesce(trim({{ column }}::text), 'N/A') || E'\n\n'
            {%- endset -%}
        {%- endif -%}
        {%- do chunks.append(chunk) -%}
    {%- endfor -%}
    
    {# Concatenate and clean final output #}
    trim(regexp_replace(
        {{ chunks | join(" || ") }},
        E'\n{3,}', E'\n\n', 'g'  -- Collapse excessive newlines
    ))
{% endmacro %}
