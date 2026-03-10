from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool
from src.services.api.rate_limit import limiter
from src.services.api.schemas import TrendingProjectOut

router = APIRouter(prefix="/recommendations")


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
