from fastapi import APIRouter, Depends

from src.services.api.database import ConnectionPool
from src.services.api.dependencies import get_pool

router = APIRouter()


@router.get("/health")
def health(pool: ConnectionPool = Depends(get_pool)) -> dict[str, str]:
    """Health check endpoint -- verifies DB connectivity."""
    with pool.get_cursor() as cur:
        cur.execute("SELECT 1")
    return {"status": "ok"}
