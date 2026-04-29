from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session

from src.services.api.dependencies import get_db, get_semantic
from src.services.api.rate_limit import RATE_LIMIT, limiter
from src.services.api.schemas import ProjectOut, ProjectSemanticOut, ProjectSimilarOut
from src.services.api.semantic import SemanticSearchService

router = APIRouter(prefix="/projects")

MAX_LIMIT = 50


def _rows(result: Result[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in result.mappings().all()]


def _row_or_none(result: Result[Any]) -> dict[str, Any] | None:
    row = result.mappings().first()
    return dict(row) if row is not None else None


@router.get("/search", response_model=list[ProjectOut])
@limiter.limit(RATE_LIMIT)
def search_projects(
    request: Request,
    q: str = Query(..., min_length=1),
    category: str | None = None,
    domain: str | None = None,
    techstack: str | None = None,
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Search projects by keyword, optionally filtered by category/domain/techstack."""
    query = """
        SELECT DISTINCT p.id, p.title, p.description, p."repoUrl" AS repo_url,
               p.published, p.trending, p."logoUrl" AS logo_url
        FROM public."Project" p
        LEFT JOIN public.project_category pc ON p.id = pc."projectId"
        LEFT JOIN public."Category" c ON pc."categoryId" = c.id
        LEFT JOIN public.project_domain pd ON p.id = pd."projectId"
        LEFT JOIN public."Domain" d ON pd."domainId" = d.id
        LEFT JOIN public.project_tech_stack pts ON p.id = pts."projectId"
        LEFT JOIN public.tech_stack ts ON pts."techStackId" = ts.id
        WHERE (p.published = true OR p.trending = true)
          AND (p.title ILIKE :title_pattern OR p.description ILIKE :description_pattern)
    """
    escaped = q.replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    params: dict[str, Any] = {
        "title_pattern": pattern,
        "description_pattern": pattern,
    }

    if category:
        query += " AND c.name = :category"
        params["category"] = category
    if domain:
        query += " AND d.name = :domain"
        params["domain"] = domain
    if techstack:
        query += " AND ts.name = :techstack"
        params["techstack"] = techstack

    query += " ORDER BY p.trending DESC, p.title LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(query), params)
    return _rows(result)


@router.get("/search-natural", response_model=list[ProjectSemanticOut])
@limiter.limit(RATE_LIMIT)
def search_natural(
    request: Request,
    q: str = Query(..., min_length=1),
    language: str | None = None,
    domain: str | None = None,
    category: str | None = None,
    techstack: str | None = None,
    limit: int = Query(default=10, ge=1, le=MAX_LIMIT),
    db: Session = Depends(get_db),
    semantic: SemanticSearchService = Depends(get_semantic),
) -> list[dict[str, Any]]:
    """Natural-language semantic search.

    Embeds the query text with the same SentenceTransformer used by the pipeline
    and ranks projects by cosine similarity against their precomputed embeddings.
    Optional hard filters narrow the candidate set before ranking.
    """
    query_vec = semantic.encode(q)
    vector_literal = "[" + ",".join(f"{v:.6f}" for v in query_vec) + "]"

    sql = """
        SELECT DISTINCT p.id, p.title, p.description, p."repoUrl" AS repo_url,
               p."logoUrl" AS logo_url,
               1 - (e.vector <=> CAST(:query_vector AS vector)) AS similarity
        FROM ml.embd_github_project e
        JOIN public."Project" p ON p.id = e."projectId"
    """
    params: dict[str, Any] = {"query_vector": vector_literal}

    if category:
        sql += (
            ' JOIN public.project_category pc ON p.id = pc."projectId"'
            ' JOIN public."Category" c ON pc."categoryId" = c.id AND c.name = :category'
        )
        params["category"] = category
    if domain:
        sql += (
            ' JOIN public.project_domain pd ON p.id = pd."projectId"'
            ' JOIN public."Domain" d ON pd."domainId" = d.id AND d.name = :domain'
        )
        params["domain"] = domain
    if techstack or language:
        sql += (
            ' JOIN public.project_tech_stack pts ON p.id = pts."projectId"'
            ' JOIN public.tech_stack ts ON pts."techStackId" = ts.id'
        )
        if techstack:
            sql += " AND ts.name = :techstack"
            params["techstack"] = techstack
        if language:
            sql += " AND ts.name ILIKE :language AND ts.type = 'LANGUAGE'"
            params["language"] = language

    sql += " WHERE (p.published = true OR p.trending = true)"
    sql += " ORDER BY similarity DESC LIMIT :limit"
    params["limit"] = limit

    result = db.execute(text(sql), params)
    return _rows(result)


@router.get("/{project_id}", response_model=ProjectOut)
@limiter.limit(RATE_LIMIT)
def get_project(
    request: Request,
    project_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get full project details by ID."""
    project = _row_or_none(
        db.execute(
            text(
                """SELECT id, title, description, "repoUrl" AS repo_url,
                          published, trending, "logoUrl" AS logo_url
                   FROM public."Project"
                   WHERE id = :project_id"""
            ),
            {"project_id": project_id},
        )
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    categories = _rows(
        db.execute(
            text(
                """SELECT c.id, c.name FROM public."Category" c
                   JOIN public.project_category pc ON c.id = pc."categoryId"
                   WHERE pc."projectId" = :project_id"""
            ),
            {"project_id": project_id},
        )
    )

    domains = _rows(
        db.execute(
            text(
                """SELECT d.id, d.name FROM public."Domain" d
                   JOIN public.project_domain pd ON d.id = pd."domainId"
                   WHERE pd."projectId" = :project_id"""
            ),
            {"project_id": project_id},
        )
    )

    tech_stacks = _rows(
        db.execute(
            text(
                """SELECT ts.id, ts.name, ts."iconUrl" AS icon_url,
                          CAST(ts.type AS text) AS type
                   FROM public.tech_stack ts
                   JOIN public.project_tech_stack pts ON ts.id = pts."techStackId"
                   WHERE pts."projectId" = :project_id"""
            ),
            {"project_id": project_id},
        )
    )

    project["categories"] = categories
    project["domains"] = domains
    project["tech_stacks"] = tech_stacks
    return project


@router.get("/{project_id}/similar", response_model=list[ProjectSimilarOut])
@limiter.limit(RATE_LIMIT)
def find_similar(
    request: Request,
    project_id: str,
    limit: int = Query(default=10, ge=1, le=MAX_LIMIT),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Find similar projects using pgvector cosine similarity."""
    embedding = _row_or_none(
        db.execute(
            text(
                """SELECT vector FROM ml.embd_github_project
                   WHERE "projectId" = :project_id"""
            ),
            {"project_id": project_id},
        )
    )
    if not embedding:
        raise HTTPException(status_code=404, detail="Project embedding not found")

    result = db.execute(
        text(
            """SELECT p.id, p.title, p.description, p."repoUrl" AS repo_url,
                      1 - (e.vector <=> ref.vector) AS similarity
               FROM ml.embd_github_project e
               JOIN ml.embd_github_project ref ON ref."projectId" = :project_id
               JOIN public."Project" p ON p.id = e."projectId"
               WHERE e."projectId" != :project_id
                 AND (p.published = true OR p.trending = true)
               ORDER BY e.vector <=> ref.vector
               LIMIT :limit"""
        ),
        {"project_id": project_id, "limit": limit},
    )
    return _rows(result)
