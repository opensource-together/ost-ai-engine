from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool, get_semantic
from src.services.api.rate_limit import limiter
from src.services.api.schemas import ProjectOut, ProjectSemanticOut, ProjectSimilarOut
from src.services.api.semantic import SemanticSearchService

router = APIRouter(prefix="/projects")

MAX_LIMIT = 50


@router.get("/search", response_model=list[ProjectOut])
@limiter.limit("60/minute")
def search_projects(
    request: Request,
    q: str = Query(..., min_length=1),
    category: str | None = None,
    domain: str | None = None,
    techstack: str | None = None,
    limit: int = Query(default=20, ge=1, le=MAX_LIMIT),
    pool: ConnectionPool = Depends(get_pool),
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
          AND (p.title ILIKE %s OR p.description ILIKE %s)
    """
    escaped = q.replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    params: list[Any] = [pattern, pattern]

    if category:
        query += " AND c.name = %s"
        params.append(category)
    if domain:
        query += " AND d.name = %s"
        params.append(domain)
    if techstack:
        query += " AND ts.name = %s"
        params.append(techstack)

    query += " ORDER BY p.trending DESC, p.title LIMIT %s"
    params.append(limit)

    with pool.get_cursor() as cur:
        cur.execute(query, params)
        return list(cur.fetchall())


@router.get("/search-natural", response_model=list[ProjectSemanticOut])
@limiter.limit("60/minute")
def search_natural(
    request: Request,
    q: str = Query(..., min_length=1),
    language: str | None = None,
    domain: str | None = None,
    category: str | None = None,
    techstack: str | None = None,
    limit: int = Query(default=10, ge=1, le=MAX_LIMIT),
    pool: ConnectionPool = Depends(get_pool),
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
               1 - (e.vector <=> %s::vector) AS similarity
        FROM ml.embd_github_project e
        JOIN public."Project" p ON p.id = e."projectId"
    """
    params: list[Any] = [vector_literal]

    if category:
        sql += (
            ' JOIN public.project_category pc ON p.id = pc."projectId"'
            ' JOIN public."Category" c ON pc."categoryId" = c.id AND c.name = %s'
        )
        params.append(category)
    if domain:
        sql += (
            ' JOIN public.project_domain pd ON p.id = pd."projectId"'
            ' JOIN public."Domain" d ON pd."domainId" = d.id AND d.name = %s'
        )
        params.append(domain)
    if techstack or language:
        sql += (
            ' JOIN public.project_tech_stack pts ON p.id = pts."projectId"'
            ' JOIN public.tech_stack ts ON pts."techStackId" = ts.id'
        )
        if techstack:
            sql += " AND ts.name = %s"
            params.append(techstack)
        if language:
            sql += " AND ts.name ILIKE %s AND ts.type = 'LANGUAGE'"
            params.append(language)

    sql += " WHERE (p.published = true OR p.trending = true)"
    sql += " ORDER BY similarity DESC LIMIT %s"
    params.append(limit)

    with pool.get_cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


@router.get("/{project_id}", response_model=ProjectOut)
@limiter.limit("60/minute")
def get_project(
    request: Request,
    project_id: str,
    pool: ConnectionPool = Depends(get_pool),
) -> dict[str, Any]:
    """Get full project details by ID."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT id, title, description, "repoUrl" AS repo_url,
                      published, trending, "logoUrl" AS logo_url
               FROM public."Project"
               WHERE id = %s""",
            (project_id,),
        )
        project = cur.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        cur.execute(
            """SELECT c.id, c.name FROM public."Category" c
               JOIN public.project_category pc ON c.id = pc."categoryId"
               WHERE pc."projectId" = %s""",
            (project_id,),
        )
        categories = cur.fetchall()

        cur.execute(
            """SELECT d.id, d.name FROM public."Domain" d
               JOIN public.project_domain pd ON d.id = pd."domainId"
               WHERE pd."projectId" = %s""",
            (project_id,),
        )
        domains = cur.fetchall()

        cur.execute(
            """SELECT ts.id, ts.name, ts."iconUrl" AS icon_url, ts.type::text
               FROM public.tech_stack ts
               JOIN public.project_tech_stack pts ON ts.id = pts."techStackId"
               WHERE pts."projectId" = %s""",
            (project_id,),
        )
        tech_stacks = cur.fetchall()

        result = dict(project)
        result["categories"] = categories
        result["domains"] = domains
        result["tech_stacks"] = tech_stacks
        return result


@router.get("/{project_id}/similar", response_model=list[ProjectSimilarOut])
@limiter.limit("60/minute")
def find_similar(
    request: Request,
    project_id: str,
    limit: int = Query(default=10, ge=1, le=MAX_LIMIT),
    pool: ConnectionPool = Depends(get_pool),
) -> list[dict[str, Any]]:
    """Find similar projects using pgvector cosine similarity."""
    with pool.get_cursor() as cur:
        cur.execute(
            'SELECT vector FROM ml.embd_github_project WHERE "projectId" = %s',
            (project_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Project embedding not found")

        cur.execute(
            """SELECT p.id, p.title, p.description, p."repoUrl" AS repo_url,
                      1 - (e.vector <=> ref.vector) AS similarity
               FROM ml.embd_github_project e
               JOIN ml.embd_github_project ref ON ref."projectId" = %s
               JOIN public."Project" p ON p.id = e."projectId"
               WHERE e."projectId" != %s
                 AND (p.published = true OR p.trending = true)
               ORDER BY e.vector <=> ref.vector
               LIMIT %s""",
            (project_id, project_id, limit),
        )
        return list(cur.fetchall())
