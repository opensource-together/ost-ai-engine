from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool


class ConnectionPool:
    """Thin wrapper around psycopg2 SimpleConnectionPool."""

    def __init__(self, database_url: str, minconn: int = 1, maxconn: int = 5) -> None:
        self._pool = SimpleConnectionPool(minconn, maxconn, database_url)

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Yield a RealDictCursor, rollback on exit, return conn to pool."""
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                yield cur
            conn.rollback()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        """Close all pooled connections."""
        self._pool.closeall()
