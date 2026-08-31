from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST

from src.api.metrics import metrics_body

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint; stays unauthenticated like /health."""
    return Response(content=metrics_body(), media_type=CONTENT_TYPE_LATEST)
