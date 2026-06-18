from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.database import build_engine_and_session_factory
from src.api.semantic import SemanticSearchService

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_semantic: SemanticSearchService | None = None


def init_db(database_url: str) -> None:
    """Initialize the global SQLAlchemy engine + session factory."""
    global _engine, _session_factory
    _engine, _session_factory = build_engine_and_session_factory(
        database_url,
        pool_size=5,
        max_overflow=0,
    )


def close_db() -> None:
    """Dispose the global SQLAlchemy engine."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a database session per request."""
    if _session_factory is None:
        raise RuntimeError("Database session factory not initialized")

    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def init_semantic() -> None:
    """Initialize the global semantic search service (eager model load)."""
    global _semantic
    if _semantic is None:
        _semantic = SemanticSearchService()


def get_semantic() -> SemanticSearchService:
    """FastAPI dependency: returns the semantic search service."""
    if _semantic is None:
        raise RuntimeError("Semantic search service not initialized")
    return _semantic
