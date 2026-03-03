-- Personalized recommendations with continuous preference scoring.
-- Replaces the old binary pre-filter with a weighted overlap score
-- blended alongside similarity, freshness, and popularity.

-- Per-user totals for each preference dimension
with user_totals as (
    select
        u.user_id,
        count(distinct uts."techStackId") as total_tech_stacks,
        count(distinct uc."categoryId")   as total_categories,
        count(distinct ud."domainId")     as total_domains
    from (
        select "userId" as user_id from {{ source('public', 'user_tech_stack') }}
        union
        select "userId" from {{ source('public', 'user_categories') }}
        union
        select "userId" from {{ source('public', 'user_domain') }}
    ) u
    left join {{ source('public', 'user_tech_stack') }} uts
        on u.user_id = uts."userId"
    left join {{ source('public', 'user_categories') }} uc
        on u.user_id = uc."userId"
    left join {{ source('public', 'user_domain') }} ud
        on u.user_id = ud."userId"
    group by u.user_id
),

-- Overlap counts per (user, project) for each dimension
tech_overlap as (
    select
        uts."userId"            as user_id,
        pts."projectId"         as project_id,
        count(*)                as shared_tech_stacks
    from {{ source('public', 'user_tech_stack') }} uts
    inner join {{ source('public', 'project_tech_stack') }} pts
        on uts."techStackId" = pts."techStackId"
    group by uts."userId", pts."projectId"
),

category_overlap as (
    select
        uc."userId"             as user_id,
        pc."projectId"          as project_id,
        count(*)                as shared_categories
    from {{ source('public', 'user_categories') }} uc
    inner join {{ source('public', 'project_category') }} pc
        on uc."categoryId" = pc."categoryId"
    group by uc."userId", pc."projectId"
),

domain_overlap as (
    select
        ud."userId"             as user_id,
        pd."projectId"          as project_id,
        count(*)                as shared_domains
    from {{ source('public', 'user_domain') }} ud
    inner join {{ source('public', 'project_domain') }} pd
        on ud."domainId" = pd."domainId"
    group by ud."userId", pd."projectId"
),

-- Merge all overlaps via UNION ALL + GROUP BY
candidate_pairs as (
    select
        user_id,
        project_id,
        coalesce(sum(shared_tech_stacks), 0) as shared_tech_stacks,
        coalesce(sum(shared_categories), 0)  as shared_categories,
        coalesce(sum(shared_domains), 0)     as shared_domains
    from (
        select user_id, project_id, shared_tech_stacks, 0 as shared_categories, 0 as shared_domains
        from tech_overlap
        union all
        select user_id, project_id, 0, shared_categories, 0
        from category_overlap
        union all
        select user_id, project_id, 0, 0, shared_domains
        from domain_overlap
    ) combined
    group by user_id, project_id
),

-- Weighted preference score with active-signal normalization.
-- If a user has 0 items in a dimension, that dimension is excluded
-- and its weight is redistributed proportionally among active signals.
preference_scored as (
    select
        cp.user_id,
        cp.project_id,
        cp.shared_tech_stacks,
        cp.shared_categories,
        cp.shared_domains,
        -- Ratios (NULL when user has no items in that dimension)
        cp.shared_tech_stacks::float  / nullif(ut.total_tech_stacks, 0) as tech_ratio,
        cp.shared_categories::float   / nullif(ut.total_categories, 0)  as cat_ratio,
        cp.shared_domains::float      / nullif(ut.total_domains, 0)     as dom_ratio,
        -- Active weight sum (only dimensions the user participates in)
        coalesce(
            case when ut.total_tech_stacks > 0 then {{ var('w_pref_tech', 0.30) }} end, 0
        ) + coalesce(
            case when ut.total_categories > 0 then {{ var('w_pref_category', 0.45) }} end, 0
        ) + coalesce(
            case when ut.total_domains > 0 then {{ var('w_pref_domain', 0.25) }} end, 0
        ) as active_weight_sum,
        -- Weighted preference score (renormalized by active weight sum)
        (
            coalesce(
                {{ var('w_pref_tech', 0.30) }}
                * cp.shared_tech_stacks::float / nullif(ut.total_tech_stacks, 0),
                0
            )
            + coalesce(
                {{ var('w_pref_category', 0.45) }}
                * cp.shared_categories::float / nullif(ut.total_categories, 0),
                0
            )
            + coalesce(
                {{ var('w_pref_domain', 0.25) }}
                * cp.shared_domains::float / nullif(ut.total_domains, 0),
                0
            )
        ) / nullif(
            coalesce(
                case when ut.total_tech_stacks > 0 then {{ var('w_pref_tech', 0.30) }} end, 0
            ) + coalesce(
                case when ut.total_categories > 0 then {{ var('w_pref_category', 0.45) }} end, 0
            ) + coalesce(
                case when ut.total_domains > 0 then {{ var('w_pref_domain', 0.25) }} end, 0
            ),
            0
        ) as preference_score
    from candidate_pairs cp
    inner join user_totals ut on cp.user_id = ut.user_id
    where
        -- At least one shared signal
        cp.shared_tech_stacks + cp.shared_categories + cp.shared_domains > 0
),

-- Vectors
user_vectors as (
    select
        "userId" as user_id,
        "vector"
    from {{ source('ml', 'embd_user') }}
),

project_vectors as (
    select
        "projectId" as project_id,
        "vector"
    from {{ source('ml', 'embd_github_project') }}
),

-- Project metadata for scoring signals
project_stats as (
    select
        id as project_id,
        stars,
        pushed_at
    from {{ ref('fct_github_project') }}
),

-- Cosine similarity on preference-filtered pairs only
similarity as (
    select
        ps.user_id,
        ps.project_id,
        ps.preference_score,
        1 - (uv.vector <=> pv.vector) as similarity_score
    from preference_scored ps
    inner join user_vectors uv on ps.user_id = uv.user_id
    inner join project_vectors pv on ps.project_id = pv.project_id
    where 1 - (uv.vector <=> pv.vector) > {{ var('similarity_threshold', 0.25) }}
),

-- Freshness: linear decay over configurable window, clamped to [0, 1]
-- Popularity: log-normalized stars, scaled to [0, 1]
max_log_stars as (
    select greatest(ln(max(stars) + 1), 1) as val
    from project_stats
),

scored as (
    select
        s.user_id,
        s.project_id,
        s.similarity_score,
        s.preference_score,
        greatest(
            0,
            1.0 - extract(epoch from (now() - ps.pushed_at))
                  / ({{ var('freshness_decay_days', 90) }} * 86400.0)
        ) as freshness_score,
        ln(ps.stars + 1) / mls.val as popularity_score
    from similarity s
    inner join project_stats ps on s.project_id = ps.project_id
    cross join max_log_stars mls
),

-- Hybrid blend: similarity + preference + freshness + popularity
blended as (
    select
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
        as final_score,
        row_number() over (
            partition by user_id
            order by
                {{ var('w_similarity', 0.40) }} * similarity_score
                + {{ var('w_preference', 0.35) }} * preference_score
                + {{ var('w_freshness', 0.15) }} * freshness_score
                + {{ var('w_popularity', 0.10) }} * popularity_score
                desc
        ) as rn
    from scored
)

select
    user_id,
    project_id,
    similarity_score,
    preference_score,
    freshness_score,
    popularity_score,
    final_score,
    now() as calculated_at
from blended
where rn <= {{ var('reco_top_n', 30) }}
