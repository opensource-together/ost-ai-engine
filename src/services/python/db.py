import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


@contextmanager
def get_db_connection(commit: bool = False) -> Generator[Any]:
    """
    Context manager for a database connection.
    Yields a connection object.

    Args:
        commit: If True, commits the transaction on success.
                If False, rolls back on exit (read-only usage).
    """
    conn = None
    try:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        conn = psycopg2.connect(db_url)
        yield conn
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_cursor(commit: bool = False) -> Generator[Any]:
    """
    Context manager for a database cursor.
    Yields a cursor object (RealDictCursor).

    Args:
        commit: If True, commits the transaction on success.
                If False, rolls back on exit (read-only usage).
    """
    with (
        get_db_connection(commit=commit) as conn,
        conn.cursor(cursor_factory=RealDictCursor) as cur,
    ):
        yield cur
