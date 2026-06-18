from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def build_engine_and_session_factory(
    database_url: str,
    pool_size: int = 5,
    max_overflow: int = 0,
) -> tuple[Engine, sessionmaker[Session]]:
    """Build the SQLAlchemy engine and session factory for the API."""
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)
