from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.rate_limit import limiter
from src.services.api.schemas import GithubTrendingProjectOut, TrendingProjectOut


router = APIRouter(prefix="/recommendations")


@router.get("/github-trending", response_model=list[GithubTrendingProjectOut])
@limiter.limit("60/minute")
def get_github_trending(
    request: Request,
    limit: int = Query(default=25, ge=1, le=50),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Get repos currently trending on GitHub."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT
                 t.repo_url, t.data, t.stars_today, t.trending_date,
                 p.id AS linked_project_id, p.name, p.description,
                 p."categoryId", p."domainId"
               FROM github.raw_trending_project t
               LEFT JOIN public."Project" p
                 ON t.repo_url = p."repoUrl"
               WHERE t.trending_date = CURRENT_DATE
               ORDER BY t.stars_today DESC NULLS LAST
               LIMIT %s""",
            (limit,),
        )
        rows = cur.fetchall()

    results = []
    for row in rows:
        data = row.get("data") or {}
        results.append(
            {
                "repo_url": row["repo_url"],
                "stars_today": row.get("stars_today"),
                "trending_date": row["trending_date"],
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "language": data.get("language"),
                "linked_project_id": row.get("linked_project_id"),
                "category_id": row.get("categoryId"),
                "domain_id": row.get("domainId"),
            }
        )
    return results

@router.get("/trending", response_model=list[TrendingProjectOut])
@limiter.limit("60/minute")
def get_trending(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Get globally trending/popular projects."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT project_id, stars, last_synced_at
               FROM public.match_global_recommendation
               ORDER BY stars DESC NULLS LAST
               LIMIT %s""",
            (limit,),
        )
        return list(cur.fetchall())
