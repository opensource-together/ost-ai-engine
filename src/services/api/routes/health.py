from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.services.api.dependencies import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Health check endpoint, checks DB connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
