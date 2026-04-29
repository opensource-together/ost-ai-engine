from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.services.api.dependencies import get_db
from src.services.api.rate_limit import limiter
from src.services.api.schemas import CategoryOut, DomainOut, TechStackOut

router = APIRouter()


def _rows(result: object) -> list[dict]:
    return [dict(row) for row in result.mappings().all()]  # type: ignore[no-any-return]


@router.get("/categories", response_model=list[CategoryOut])
@limiter.limit("60/minute")
def list_categories(
    request: Request, db: Session = Depends(get_db)
) -> list[dict]:
    """List all project categories."""
    result = db.execute(text('SELECT id, name FROM public."Category" ORDER BY name'))
    return _rows(result)


@router.get("/domains", response_model=list[DomainOut])
@limiter.limit("60/minute")
def list_domains(
    request: Request, db: Session = Depends(get_db)
) -> list[dict]:
    """List all project domains."""
    result = db.execute(text('SELECT id, name FROM public."Domain" ORDER BY name'))
    return _rows(result)


@router.get("/techstacks", response_model=list[TechStackOut])
@limiter.limit("60/minute")
def list_techstacks(
    request: Request, db: Session = Depends(get_db)
) -> list[dict]:
    """List all tech stacks."""
    result = db.execute(
        text(
            """SELECT id, name, "iconUrl" AS icon_url, CAST(type AS text) AS type
               FROM public.tech_stack
               ORDER BY name"""
        )
    )
    return _rows(result)
