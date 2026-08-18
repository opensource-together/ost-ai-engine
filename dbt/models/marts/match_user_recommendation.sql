-- Personalized recommendations: retrieve from three sources, filter, then one score.
-- Sources (X For You-style): preference overlap, embedding neighbors, global trending.

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
        SELECT
            "userId",
            count(*) AS total_tech_stacks
        FROM {{ source('public', 'user_tech_stack') }}
        GROUP BY "userId"
    ) AS t ON u.user_id = t."userId"
    LEFT JOIN (
        SELECT
            "userId",
            count(*) AS total_categories
        FROM {{ source('public', 'user_categories') }}
        GROUP BY "userId"
    ) AS c ON u.user_id = c."userId"
    LEFT JOIN (
        SELECT
            "userId",
            count(*) AS total_domains
        FROM {{ source('public', 'user_domain') }}
        GROUP BY "userId"
    ) AS d ON u.user_id = d."userId"
),

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

preference_raw AS (
    SELECT
        cp.user_id,
        cp.project_id,
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
    WHERE cp.shared_tech_stacks + cp.shared_categories + cp.shared_domains > 0
),

-- Visibility (rank vs show): published/trending, has a real README, language signal.
visible_projects AS (
    SELECT
        p.id AS project_id,
        f.stars,
        f.pushed_at,
        f.language_confidence
    FROM {{ source('public', 'Project') }} AS p
    INNER JOIN {{ ref('fct_github_project') }} AS f ON p.id::uuid = f.id
    INNER JOIN {{ ref('stg_github__readme') }} AS r ON f.id = r.project_id
    WHERE
        (p.published = true OR p.trending = true)
        AND length(trim(r.content)) >= {{ var('min_readme_chars', 50) }}
        AND coalesce(f.language_confidence, 0) >= {{ var('min_language_confidence', 0.3) }}
),

user_shown_ignored AS (
    SELECT
        shown.user_id,
        shown.project_id
    FROM (
        SELECT
            user_id,
            project_id,
            count(*) AS n_shown
        FROM {{ ref('stg_public__recommendation_event') }}
        WHERE
            event_type = 'SHOWN'
            AND occurred_at >= now() - interval '{{ var("ignored_lookback_days", 30) }} days'
        GROUP BY user_id, project_id
    ) AS shown
    LEFT JOIN (
        SELECT DISTINCT
            user_id,
            project_id
        FROM {{ ref('stg_public__recommendation_event') }}
        WHERE
            event_type IN ('CLICKED', 'STARRED_AFTER_RECO')
            AND occurred_at >= now() - interval '{{ var("ignored_lookback_days", 30) }} days'
    ) AS clicked
        ON shown.user_id = clicked.user_id AND shown.project_id = clicked.project_id
    WHERE
        clicked.project_id IS null
        AND shown.n_shown >= {{ var('ignored_min_shown', 3) }}
),

user_bookmarks AS (
    SELECT
        user_id,
        project_id
    FROM {{ ref('stg_public__project_bookmark') }}
),

user_vectors AS (
    SELECT
        "userId" AS user_id,
        vector
    FROM {{ source('ml', 'embd_user') }}
),

project_vectors AS (
    SELECT
        e."projectId" AS project_id,
        e.vector
    FROM {{ source('ml', 'embd_github_project') }} AS e
    INNER JOIN visible_projects AS vp ON e."projectId" = vp.project_id
),

reco_users AS (
    SELECT user_id FROM user_totals
    UNION
    SELECT user_id FROM user_vectors
),

src_preference AS (
    SELECT
        pr.user_id,
        pr.project_id
    FROM preference_raw AS pr
    INNER JOIN visible_projects AS vp ON pr.project_id = vp.project_id
),

similarity_ranked AS (
    SELECT
        uv.user_id,
        pv.project_id,
        row_number() OVER (
            PARTITION BY uv.user_id
            ORDER BY uv.vector <=> pv.vector
        ) AS sim_rn
    FROM user_vectors AS uv
    CROSS JOIN project_vectors AS pv
    WHERE 1 - (uv.vector <=> pv.vector) > {{ var('similarity_threshold', 0.25) }}
),

src_similarity AS (
    SELECT
        user_id,
        project_id
    FROM similarity_ranked
    WHERE sim_rn <= {{ var('similarity_source_top_n', 50) }}
),

src_trending AS (
    SELECT
        ru.user_id,
        g.project_id
    FROM reco_users AS ru
    CROSS JOIN {{ ref('match_global_recommendation') }} AS g
    INNER JOIN visible_projects AS vp ON g.project_id = vp.project_id
),

candidates AS (
    SELECT
        s.user_id,
        s.project_id
    FROM (
        SELECT
            user_id,
            project_id
        FROM src_preference
        UNION
        SELECT
            user_id,
            project_id
        FROM src_similarity
        UNION
        SELECT
            user_id,
            project_id
        FROM src_trending
    ) AS s
    LEFT JOIN user_shown_ignored AS usi
        ON s.user_id = usi.user_id AND s.project_id = usi.project_id
    LEFT JOIN user_bookmarks AS ub
        ON s.user_id = ub.user_id AND s.project_id = ub.project_id
    WHERE
        usi.project_id IS null
        AND ub.project_id IS null
),

max_log_stars AS (
    SELECT greatest(ln(max(stars) + 1), 1) AS val
    FROM visible_projects
),

scored AS (
    SELECT
        c.user_id,
        c.project_id,
        {{ clamp('coalesce(1 - (uv.vector <=> pv.vector), 0)') }} AS similarity_score,
        coalesce(pr.preference_score, 0) AS preference_score,
        ({{ clamp(
            '1.0 - extract(EPOCH FROM (now() - vp.pushed_at)) / ('
            ~ var('freshness_decay_days', 90) ~ ' * 86400.0)'
        ) }})::double precision AS freshness_score,
        {{ clamp('ln(vp.stars + 1) / mls.val') }} AS popularity_score
    FROM candidates AS c
    INNER JOIN visible_projects AS vp ON c.project_id = vp.project_id
    CROSS JOIN max_log_stars AS mls
    LEFT JOIN preference_raw AS pr
        ON c.user_id = pr.user_id AND c.project_id = pr.project_id
    LEFT JOIN user_vectors AS uv ON c.user_id = uv.user_id
    LEFT JOIN project_vectors AS pv ON c.project_id = pv.project_id
),

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
            AS final_score
    FROM scored
),

project_primary_category AS (
    SELECT DISTINCT ON ("projectId")
        "projectId" AS project_id,
        "categoryId" AS category_id
    FROM {{ source('public', 'project_category') }}
    ORDER BY "projectId", "categoryId"
),

diversified AS (
    SELECT
        b.user_id,
        b.project_id,
        b.similarity_score,
        b.preference_score,
        b.freshness_score,
        b.popularity_score,
        b.final_score,
        b.final_score * power(
            {{ var('category_diversity_decay', 0.7) }},
            (row_number() OVER (
                PARTITION BY b.user_id, coalesce(ppc.category_id::text, b.project_id::text)
                ORDER BY b.final_score DESC
            ) - 1)
        ) AS rank_score
    FROM blended AS b
    LEFT JOIN project_primary_category AS ppc ON b.project_id = ppc.project_id
),

ranked AS (
    SELECT
        user_id,
        project_id,
        similarity_score,
        preference_score,
        freshness_score,
        popularity_score,
        final_score,
        row_number() OVER (
            PARTITION BY user_id
            ORDER BY rank_score DESC, final_score DESC
        ) AS rn
    FROM diversified
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
FROM ranked
WHERE rn <= {{ var('reco_top_n', 30) }}
