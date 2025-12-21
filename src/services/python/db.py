import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """
    Context manager for a database connection.
    Yields a connection object.
    """
    conn = None
    try:
        # Connect to the database using the DATABASE_URL environment variable
        # or fallback to a default if not set (though it should be set)
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        conn = psycopg2.connect(db_url)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for a database cursor.
    Yields a cursor object (RealDictCursor).
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur


