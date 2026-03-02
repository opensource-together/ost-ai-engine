-- Pre-filter: only score projects that share at least one preference with the user
with tech_stack_pairs as (
    select
        uts."userId" as user_id,
        pts."projectId" as project_id
    from {{ source('public', 'user_tech_stack') }} uts
    inner join {{ source('public', 'project_tech_stack') }} pts
        on uts."techStackId" = pts."techStackId"
),

domain_pairs as (
    select
        ud."userId" as user_id,
        pd."projectId" as project_id
    from {{ source('public', 'user_domain') }} ud
    inner join {{ source('public', 'project_domain') }} pd
        on ud."domainId" = pd."domainId"
),

category_pairs as (
    select
        uc."userId" as user_id,
        pc."projectId" as project_id
    from {{ source('public', 'user_categories') }} uc
    inner join {{ source('public', 'project_category') }} pc
        on uc."categoryId" = pc."categoryId"
),

-- Deduplicated candidate pairs from all preference signals
candidate_pairs as (
    select distinct user_id, project_id
    from (
        select user_id, project_id from tech_stack_pairs
        union all
        select user_id, project_id from domain_pairs
        union all
        select user_id, project_id from category_pairs
    ) combined
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

-- Cosine similarity on pre-filtered pairs only
similarity as (
    select
        cp.user_id,
        cp.project_id,
        1 - (uv.vector <=> pv.vector) as similarity_score
    from candidate_pairs cp
    inner join user_vectors uv on cp.user_id = uv.user_id
    inner join project_vectors pv on cp.project_id = pv.project_id
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

-- Hybrid blend
blended as (
    select
        user_id,
        project_id,
        similarity_score,
        freshness_score,
        popularity_score,
        {{ var('w_similarity', 0.6) }} * similarity_score
        + {{ var('w_freshness', 0.2) }} * freshness_score
        + {{ var('w_popularity', 0.2) }} * popularity_score
        as final_score,
        row_number() over (
            partition by user_id
            order by
                {{ var('w_similarity', 0.6) }} * similarity_score
                + {{ var('w_freshness', 0.2) }} * freshness_score
                + {{ var('w_popularity', 0.2) }} * popularity_score
                desc
        ) as rn
    from scored
)

select
    user_id,
    project_id,
    similarity_score,
    freshness_score,
    popularity_score,
    final_score,
    now() as calculated_at
from blended
where rn <= {{ var('reco_top_n', 30) }}
