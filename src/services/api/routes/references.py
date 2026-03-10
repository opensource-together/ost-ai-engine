from fastapi import APIRouter, Depends

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.schemas import CategoryOut, DomainOut, TechStackOut

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(pool: ConnectionPool = Depends(get_pool)) -> list[dict]:
    """List all project categories."""
    with pool.get_cursor() as cur:
        cur.execute('SELECT id, name FROM public."Category" ORDER BY name')
        return cur.fetchall()


@router.get("/domains", response_model=list[DomainOut])
def list_domains(pool: ConnectionPool = Depends(get_pool)) -> list[dict]:
    """List all project domains."""
    with pool.get_cursor() as cur:
        cur.execute('SELECT id, name FROM public."Domain" ORDER BY name')
        return cur.fetchall()


@router.get("/techstacks", response_model=list[TechStackOut])
def list_techstacks(pool: ConnectionPool = Depends(get_pool)) -> list[dict]:
    """List all tech stacks."""
    with pool.get_cursor() as cur:
        cur.execute(
            """SELECT id, name, "iconUrl" AS icon_url, type
               FROM public.tech_stack
               ORDER BY name"""
        )
        return cur.fetchall()
