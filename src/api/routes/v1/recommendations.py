import json
from typing import Any
from uuid import UUID

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.rate_limit import RATE_LIMIT, limiter
from src.api.row_mapping import mapping_row_first, mapping_rows
from src.api.schemas import (
    ForYouProjectOut,
    GithubTrendingProjectOut,
    TrendingProjectOut,
)
from src.linker.recommendation.mmr import select_mmr

router = APIRouter(prefix="/recommendations")


def _parse_embedding(value: object) -> np.ndarray | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    try:
        embedding = np.asarray(value, dtype=float)
    except (TypeError, ValueError, OverflowError):
        return None
    if embedding.ndim != 1 or embedding.size == 0 or not np.isfinite(embedding).all():
        return None
    norm = np.linalg.norm(embedding)
    if not np.isfinite(norm) or norm == 0:
        return None
    return embedding


def _mmr_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    parsed_rows: list[dict[str, Any]] = []
    dimension: int | None = None
    for row in rows:
        embedding = _parse_embedding(row.get("embedding"))
        if embedding is None:
            return None
        if dimension is None:
            dimension = len(embedding)
        elif len(embedding) != dimension:
            return None
        parsed_rows.append({**row, "embedding": embedding})
    return parsed_rows


def _public_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in row.items() if key != "embedding"} for row in rows
    ]


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


@router.get("/for-you", response_model=list[ForYouProjectOut])
@limiter.limit(RATE_LIMIT)
def get_for_you(
    request: Request,
    user_id: UUID = Query(...),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Personalized recommendations from match_user_recommendation."""
    user = mapping_row_first(
        db.execute(
            text('SELECT id FROM public."user" WHERE id = :user_id'),
            {"user_id": str(user_id)},
        )
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = db.execute(
        text(
            """SELECT
                 mur.project_id,
                 p.title,
                 p.description,
                 p."repoUrl" AS repo_url,
                 mur.similarity_score,
                 mur.preference_score,
                 mur.freshness_score,
                 mur.popularity_score,
                 mur.final_score,
                 e.vector AS embedding
               FROM public.match_user_recommendation AS mur
               INNER JOIN public."Project" AS p ON p.id = mur.project_id
               LEFT JOIN ml.embd_github_project AS e
                 ON e."projectId" = mur.project_id
               WHERE mur.user_id = :user_id
               ORDER BY mur.final_score DESC
               LIMIT :limit"""
        ),
        {"user_id": str(user_id), "limit": 3 * limit},
    )
    rows = mapping_rows(result)
    candidates = _mmr_candidates(rows)
    if candidates is None:
        return _public_rows(rows[:limit])
    selected = select_mmr(candidates, limit=limit)
    return _public_rows([dict(candidate) for candidate in selected])
