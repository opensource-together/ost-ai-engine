from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.services.api.dependencies import get_db
from src.services.api.rate_limit import RATE_LIMIT, limiter
from src.services.api.row_mapping import mapping_rows
from src.services.api.schemas import GithubTrendingProjectOut, TrendingProjectOut

router = APIRouter(prefix="/recommendations")


@router.get("/github-trending", response_model=list[GithubTrendingProjectOut])
@limiter.limit(RATE_LIMIT)
def get_github_trending(
    request: Request,
    limit: int = Query(default=25, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get repos currently trending on GitHub."""
    result = db.execute(
        text(
            """SELECT
                 t.repo_url, t.data, t.stars_today, t.trending_date,
                 p.id AS linked_project_id, p.name, p.description,
                 p."categoryId", p."domainId"
               FROM github.raw_trending_project t
               LEFT JOIN public."Project" p
                 ON t.repo_url = p."repoUrl"
               WHERE t.trending_date = CURRENT_DATE
               ORDER BY t.stars_today DESC NULLS LAST
               LIMIT :limit"""
        ),
        {"limit": limit},
    )
    rows = mapping_rows(result)

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
@limiter.limit(RATE_LIMIT)
def get_trending(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get globally trending/popular projects."""
    result = db.execute(
        text(
            """SELECT project_id, stars, last_synced_at
               FROM public.match_global_recommendation
               ORDER BY stars DESC NULLS LAST
               LIMIT :limit"""
        ),
        {"limit": limit},
    )
    return mapping_rows(result)
