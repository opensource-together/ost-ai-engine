import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables from a .env file
load_dotenv()

# --- Database Configuration ---
# It's recommended to get this from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
# --- Engine & Session ---

# The engine is the entry point to the database.
# It's a factory for connections.
engine = create_engine(DATABASE_URL)

# The sessionmaker is a factory for creating Session objects.
# The Session is our "handle" to the database for making queries.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function to get a database session.
    This ensures that the database session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 