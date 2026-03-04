WITH raw_user AS (
    SELECT * FROM {{ ref('int_user_enriched') }}
)

SELECT
    user_id,
    {{ build_user_context([
        ('Full Name', 'name'),
        ('Bio', 'bio'),
        ('Job Title', 'job_title'),
        ('Tech Stacks', 'tech_stacks'),
        ('Domains', 'domains'),
        ('Interests', 'categories'),
        ('Experience', 'experiences::text')
    ]) }} AS user_context
FROM raw_user
