from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.infrastructure.config import settings

# The pytest-dotenv plugin now handles loading the .env file automatically for tests.
# Pydantic's settings will handle it for other environments.
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency to get a database session.
    Ensures the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
