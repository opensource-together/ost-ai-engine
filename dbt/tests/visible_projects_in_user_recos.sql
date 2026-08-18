-- Recos must only include published or trending public projects (visibility).
SELECT
    mur.user_id,
    mur.project_id
FROM {{ ref('match_user_recommendation') }} AS mur
INNER JOIN {{ source('public', 'Project') }} AS p ON mur.project_id = p.id
WHERE p.published = false AND p.trending = false
