import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from src.infrastructure.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Enhanced database engine with connection pooling and error handling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before use
    echo=False,
    connect_args={"connect_timeout": 10, "application_name": "ost-data-engine"},
)

# Enhanced session factory with error handling
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent lazy loading issues
)

Base = declarative_base()


def get_db():
    """
    Dependency to get a database session.
    Ensures the session is always closed after the request.
    Enhanced with error handling and logging.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database session: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Provides automatic cleanup and error handling.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error in session: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database session: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def test_database_connection():
    """
    Test database connection and log status.
    """
    try:
        with get_db_session() as db:
            # Simple query to test connection
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def get_database_stats():
    """
    Get database connection pool statistics.
    """
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": getattr(
                pool, "invalid", 0
            ),  # Handle missing attribute gracefully
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}


def close_database_connections():
    """
    Close all database connections.
    Useful for cleanup during shutdown.
    """
    try:
        engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Failed to close database connections: {e}")
