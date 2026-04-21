from src.services.api.database import ConnectionPool
from src.services.api.semantic import SemanticSearchService

_pool: ConnectionPool | None = None
_semantic: SemanticSearchService | None = None



def init_pool(database_url: str) -> None:
    """Initialize the global connection pool."""
    global _pool
    _pool = ConnectionPool(database_url, minconn=1, maxconn=5)


def close_pool() -> None:
    """Close the global connection pool."""
    if _pool:
        _pool.close()


def get_pool() -> ConnectionPool:
    """FastAPI dependency: returns the connection pool."""
    if _pool is None:
        raise RuntimeError("Connection pool not initialized")
    return _pool
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

