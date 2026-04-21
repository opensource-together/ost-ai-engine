-- Ensure no (user_id, project_id) pair appears in recommendations
-- if the user has already bookmarked that project.
SELECT
    mur.user_id,
    mur.project_id
FROM {{ ref('match_user_recommendation') }} AS mur
INNER JOIN {{ ref('stg_public__project_bookmark') }} AS pb
    ON mur.user_id = pb.user_id AND mur.project_id = pb.project_id
