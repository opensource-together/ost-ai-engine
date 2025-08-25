"""
Recreate the database schema based on SQLAlchemy models.

This script connects to the database, drops all known tables, and
recreates them based on the current definitions in `src/domain/models/schema.py`.

It's an essential tool for development when making schema changes without
a full migration system like Alembic.

Usage:
    - Ensure your .env file is configured with the correct DATABASE_URL.
    - Run from the project root: `poetry run python scripts/database/recreate_schema.py`
"""
import sys
import os

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.infrastructure.postgres.database import engine, get_db_session
from src.domain.models.schema import Base
from src.infrastructure.config import settings
import logging as logger
from sqlalchemy import text

logger.basicConfig(level=logger.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def recreate_database_schema():
    """
    Drops the public schema and all its objects, then recreates it
    and all tables defined in the Base metadata.
    """
    if "prod" in settings.DATABASE_URL.lower():
        confirm = input(
            "⚠️ WARNING: You are about to drop and recreate all tables in a PRODUCTION environment.\n"
            "This is a destructive operation. Are you sure you want to continue? (y/n): "
        )
        if confirm.lower() != 'y':
            logger.info("Operation cancelled by user.")
            return

    logger.info("Connecting to the database...")
    try:
        with engine.connect() as connection:
            logger.info("Database connection successful.")
            logger.info("Dropping public schema with CASCADE...")
            try:
                connection.execute(text("COMMIT")) # End any existing transaction
                connection.execute(text("DROP SCHEMA public CASCADE;"))
                connection.execute(text("CREATE SCHEMA public;"))
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
                logger.info("✅ Public schema dropped and recreated successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to drop/recreate public schema: {e}")
                connection.execute(text("ROLLBACK"))
                return

            logger.info("Creating new tables based on the schema...")
            try:
                Base.metadata.create_all(bind=engine)
                logger.info("✅ All tables created successfully!")

                logger.info("Ensuring staging table 'github_PROJECT' exists...")
                create_staging_table_sql = text("""
                    CREATE TABLE IF NOT EXISTS "github_PROJECT" (
                        full_name TEXT PRIMARY KEY,
                        name TEXT,
                        owner TEXT,
                        description TEXT,
                        fork BOOLEAN,
                        language TEXT,
                        stargazers_count INTEGER,
                        watchers_count INTEGER,
                        forks_count INTEGER,
                        open_issues_count INTEGER,
                        topics TEXT[],
                        archived BOOLEAN,
                        disabled BOOLEAN,
                        created_at TIMESTAMPTZ,
                        updated_at TIMESTAMPTZ,
                        pushed_at TIMESTAMPTZ,
                        homepage TEXT,
                        license TEXT,
                        languages_map JSONB,
                        readme TEXT,
                        raw JSONB,
                        last_ingested_at TIMESTAMPTZ
                    );
                """)
                connection.execute(create_staging_table_sql)
                logger.info("✅ Staging table 'github_PROJECT' is ready.")

            except Exception as e:
                logger.error(f"❌ Failed to create tables: {e}")
                return

    except Exception as e:
        logger.error(f"❌ Failed to connect to the database: {e}")
        logger.error("Please check your DATABASE_URL in your .env file and ensure the database container is running.")
        return

if __name__ == "__main__":
    recreate_database_schema()
