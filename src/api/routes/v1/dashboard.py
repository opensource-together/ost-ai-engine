from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.api.dashboard import load_dashboard, render_dashboard_html
from src.api.dependencies import get_db
from src.api.rate_limit import RATE_LIMIT, limiter
from src.api.schemas import DashboardOut

router = APIRouter(prefix="/dashboard")


@router.get("", response_model=DashboardOut)
@limiter.limit(RATE_LIMIT)
def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
) -> DashboardOut:
    """JSON snapshot of catalog, feedback and ranker quality KPIs."""
    return load_dashboard(db)


@router.get("/ui", response_class=HTMLResponse)
@limiter.limit(RATE_LIMIT)
def get_dashboard_ui(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """HTML view of the same KPI snapshot."""
    return HTMLResponse(render_dashboard_html(load_dashboard(db)))
