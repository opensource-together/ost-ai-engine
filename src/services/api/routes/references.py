from fastapi import APIRouter, Depends, Request

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.rate_limit import limiter
from src.services.api.schemas import CategoryOut, DomainOut, TechStackOut

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
@limiter.limit("60/minute")
def list_categories(
    request: Request, pool: ConnectionPool = Depends(get_pool)
) -> list[dict]:
    """List all project categories."""
    with pool.get_cursor() as cur:
        cur.execute('SELECT id, name FROM public."Category" ORDER BY name')
        return list(cur.fetchall())


@router.get("/domains", response_model=list[DomainOut])
@limiter.limit("60/minute")
def list_domains(
    request: Request, pool: ConnectionPool = Depends(get_pool)
) -> list[dict]:
    """List all project domains."""
    with pool.get_cursor() as cur:
        cur.execute('SELECT id, name FROM public."Domain" ORDER BY name')
        return list(cur.fetchall())


@router.get("/techstacks", response_model=list[TechStackOut])
@limiter.limit("60/minute")
def list_techstacks(
    request: Request, pool: ConnectionPool = Depends(get_pool)
) -> list[dict]:
    """List all tech stacks."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT id, name, "iconUrl" AS icon_url, type::text
               FROM public.tech_stack
               ORDER BY name"""
        )
        return list(cur.fetchall())
