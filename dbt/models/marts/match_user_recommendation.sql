-- Personalized recommendations with continuous preference scoring.
-- Replaces the old binary pre-filter with a weighted overlap score
-- blended alongside similarity, freshness, and popularity.

-- Per-user totals for each preference dimension
-- Pre-aggregate each junction table before joining to avoid row explosion.
WITH user_totals AS (
    SELECT
        u.user_id,
        coalesce(t.total_tech_stacks, 0) AS total_tech_stacks,
        coalesce(c.total_categories, 0) AS total_categories,
        coalesce(d.total_domains, 0) AS total_domains
    FROM (
        SELECT "userId" AS user_id FROM {{ source('public', 'user_tech_stack') }}
        UNION
        SELECT "userId" FROM {{ source('public', 'user_categories') }}
        UNION
        SELECT "userId" FROM {{ source('public', 'user_domain') }}
    ) AS u
    LEFT JOIN (
        SELECT "userId", count(*) AS total_tech_stacks
        FROM {{ source('public', 'user_tech_stack') }}
        GROUP BY "userId"
    ) AS t ON u.user_id = t."userId"
    LEFT JOIN (
        SELECT "userId", count(*) AS total_categories
        FROM {{ source('public', 'user_categories') }}
        GROUP BY "userId"
    ) AS c ON u.user_id = c."userId"
    LEFT JOIN (
        SELECT "userId", count(*) AS total_domains
        FROM {{ source('public', 'user_domain') }}
        GROUP BY "userId"
    ) AS d ON u.user_id = d."userId"
),

-- Overlap counts per (user, project) for each dimension
tech_overlap AS (
    SELECT
        uts."userId" AS user_id,
        pts."projectId" AS project_id,
        count(*) AS shared_tech_stacks
    FROM {{ source('public', 'user_tech_stack') }} AS uts
    INNER JOIN {{ source('public', 'project_tech_stack') }} AS pts
        ON uts."techStackId" = pts."techStackId"
    GROUP BY uts."userId", pts."projectId"
),

category_overlap AS (
    SELECT
        uc."userId" AS user_id,
        pc."projectId" AS project_id,
        count(*) AS shared_categories
    FROM {{ source('public', 'user_categories') }} AS uc
    INNER JOIN {{ source('public', 'project_category') }} AS pc
        ON uc."categoryId" = pc."categoryId"
    GROUP BY uc."userId", pc."projectId"
),

domain_overlap AS (
    SELECT
        ud."userId" AS user_id,
        pd."projectId" AS project_id,
        count(*) AS shared_domains
    FROM {{ source('public', 'user_domain') }} AS ud
    INNER JOIN {{ source('public', 'project_domain') }} AS pd
        ON ud."domainId" = pd."domainId"
    GROUP BY ud."userId", pd."projectId"
),

-- Merge all overlaps via UNION ALL + GROUP BY
candidate_pairs AS (
    SELECT
        user_id,
        project_id,
        coalesce(sum(shared_tech_stacks), 0) AS shared_tech_stacks,
        coalesce(sum(shared_categories), 0) AS shared_categories,
        coalesce(sum(shared_domains), 0) AS shared_domains
    FROM (
        SELECT
            user_id,
            project_id,
            shared_tech_stacks,
            0 AS shared_categories,
            0 AS shared_domains
        FROM tech_overlap
        UNION ALL
        SELECT
            user_id,
            project_id,
            0 AS shared_tech_stacks,
            shared_categories,
            0 AS shared_domains
        FROM category_overlap
        UNION ALL
        SELECT
            user_id,
            project_id,
            0 AS shared_tech_stacks,
            0 AS shared_categories,
            shared_domains
        FROM domain_overlap
    ) AS combined
    GROUP BY user_id, project_id
),

-- Weighted preference score with active-signal normalization.
-- If a user has 0 items in a dimension, that dimension is excluded
-- and its weight is redistributed proportionally among active signals.
preference_scored AS (
    SELECT
        cp.user_id,
        cp.project_id,
        cp.shared_tech_stacks,
        cp.shared_categories,
        cp.shared_domains,
        -- Ratios (NULL when user has no items in that dimension)
        {{ safe_divide('cp.shared_tech_stacks', 'ut.total_tech_stacks') }} AS tech_ratio,
        {{ safe_divide('cp.shared_categories', 'ut.total_categories') }} AS cat_ratio,
        {{ safe_divide('cp.shared_domains', 'ut.total_domains') }} AS dom_ratio,
        -- Active weight sum (only dimensions the user participates in)
        coalesce(
            CASE WHEN ut.total_tech_stacks > 0 THEN {{ var('w_pref_tech', 0.30) }} END, 0
        ) + coalesce(
            CASE WHEN ut.total_categories > 0 THEN {{ var('w_pref_category', 0.45) }} END, 0
        ) + coalesce(
            CASE WHEN ut.total_domains > 0 THEN {{ var('w_pref_domain', 0.25) }} END, 0
        ) AS active_weight_sum,
        -- Weighted preference score (renormalized by active weight sum)
        (
            coalesce(
                {{ var('w_pref_tech', 0.30) }}
                * {{ safe_divide('cp.shared_tech_stacks', 'ut.total_tech_stacks') }},
                0
            )
            + coalesce(
                {{ var('w_pref_category', 0.45) }}
                * {{ safe_divide('cp.shared_categories', 'ut.total_categories') }},
                0
            )
            + coalesce(
                {{ var('w_pref_domain', 0.25) }}
                * {{ safe_divide('cp.shared_domains', 'ut.total_domains') }},
                0
            )
        ) / nullif(
            coalesce(
                CASE WHEN ut.total_tech_stacks > 0 THEN {{ var('w_pref_tech', 0.30) }} END, 0
            ) + coalesce(
                CASE WHEN ut.total_categories > 0 THEN {{ var('w_pref_category', 0.45) }} END, 0
            ) + coalesce(
                CASE WHEN ut.total_domains > 0 THEN {{ var('w_pref_domain', 0.25) }} END, 0
            ),
            0
        ) AS preference_score
    FROM candidate_pairs AS cp
    INNER JOIN user_totals AS ut ON cp.user_id = ut.user_id
    WHERE
        -- At least one shared signal
        cp.shared_tech_stacks + cp.shared_categories + cp.shared_domains > 0
),

-- Vectors
user_vectors AS (
    SELECT
        "userId" AS user_id,
        vector
    FROM {{ source('ml', 'embd_user') }}
),

project_vectors AS (
    SELECT
        "projectId" AS project_id,
        vector
    FROM {{ source('ml', 'embd_github_project') }}
),

-- Project metadata for scoring signals
project_stats AS (
    SELECT
        id AS project_id,
        stars,
        pushed_at
    FROM {{ ref('fct_github_project') }}
),

-- Cosine similarity on preference-filtered pairs only
similarity AS (
    SELECT
        ps.user_id,
        ps.project_id,
        ps.preference_score,
        1 - (uv.vector <=> pv.vector) AS similarity_score
    FROM preference_scored AS ps
    INNER JOIN user_vectors AS uv ON ps.user_id = uv.user_id
    INNER JOIN project_vectors AS pv ON ps.project_id = pv.project_id
    WHERE 1 - (uv.vector <=> pv.vector) > {{ var('similarity_threshold', 0.25) }}
),

-- Freshness: linear decay over configurable window, clamped to [0, 1]
-- Popularity: log-normalized stars, scaled to [0, 1]
max_log_stars AS (
    SELECT greatest(ln(max(stars) + 1), 1) AS val
    FROM project_stats
),

scored AS (
    SELECT
        s.user_id,
        s.project_id,
        s.similarity_score,
        s.preference_score,
        ({{ clamp(
            '1.0 - extract(EPOCH FROM (now() - ps.pushed_at)) / (' ~ var('freshness_decay_days', 90) ~ ' * 86400.0)'
        ) }})::double precision AS freshness_score,
        {{ clamp('ln(ps.stars + 1) / mls.val') }} AS popularity_score
    FROM similarity AS s
    INNER JOIN project_stats AS ps ON s.project_id = ps.project_id
    CROSS JOIN max_log_stars AS mls
),

-- Hybrid blend: similarity + preference + freshness + popularity
blended AS (
    SELECT
        user_id,
        project_id,
        similarity_score,
        preference_score,
        freshness_score,
        popularity_score,
        {{ var('w_similarity', 0.40) }} * similarity_score
        + {{ var('w_preference', 0.35) }} * preference_score
        + {{ var('w_freshness', 0.15) }} * freshness_score
        + {{ var('w_popularity', 0.10) }} * popularity_score
            AS final_score,
        row_number() OVER (
            PARTITION BY user_id
            ORDER BY
                {{ var('w_similarity', 0.40) }} * similarity_score
                + {{ var('w_preference', 0.35) }} * preference_score
                + {{ var('w_freshness', 0.15) }} * freshness_score
                + {{ var('w_popularity', 0.10) }} * popularity_score
                DESC
        ) AS rn
    FROM scored
)

SELECT
    user_id,
    project_id,
    similarity_score,
    preference_score,
    freshness_score,
    popularity_score,
    final_score,
    now() AS calculated_at
FROM blended
WHERE rn <= {{ var('reco_top_n', 30) }}
