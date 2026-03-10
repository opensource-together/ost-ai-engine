from src.services.api.database import ConnectionPool

_pool: ConnectionPool | None = None


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
