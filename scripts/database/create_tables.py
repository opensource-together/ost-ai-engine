#!/usr/bin/env python3
"""
Database Table Creation Script

This script creates all database tables from the schema definition.
Uses classes for better organization and maintainability.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.infrastructure.postgres.database import SessionLocal, engine
from src.domain.models.schema import Base
from src.infrastructure.logger import log


class TableCreator:
    """Handles creation of all database tables."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def create_all_tables(self):
        """Create all tables using SQLAlchemy Base.metadata.create_all()."""
        log.info("Creating all database tables...")
        
        try:
            # This will create all tables defined in the schema
            Base.metadata.create_all(bind=engine)
            log.info("✅ All tables created successfully")
            
            # Verify tables were created
            self._verify_tables()
            
        except Exception as e:
            log.error(f"❌ Error creating tables: {e}")
            raise
    
    def _verify_tables(self):
        """Verify that all expected tables were created."""
        log.info("Verifying table creation...")
        
        expected_tables = [
            "USER", "USER_GITHUB_CREDENTIALS", "PROJECT", "PROJECT_EXTERNAL_LINK",
            "TECH_STACK", "TEAM_MEMBER", "PROJECT_ROLE", "PROJECT_ROLE_APPLICATION",
            "USER_SOCIAL_LINK", "CATEGORY", "KEY_FEATURE", "PROJECT_GOAL",
            # Association tables
            "PROJECT_TECH_STACK", "USER_TECH_STACK", "PROJECT_CATEGORY",
            "PROJECT_ROLE_TECH_STACK", "TEAM_MEMBER_PROJECT_ROLE",
            "PROJECT_ROLE_APPLICATION_KEY_FEATURE", "PROJECT_ROLE_APPLICATION_PROJECT_GOAL"
        ]
        
        try:
            # Check if tables exist by querying information_schema
            result = self.db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            existing_tables = [row[0] for row in result]
            log.info(f"Found {len(existing_tables)} tables in database")
            
            missing_tables = [table for table in expected_tables if table not in existing_tables]
            
            if missing_tables:
                log.warning(f"⚠️ Missing tables: {missing_tables}")
            else:
                log.info("✅ All expected tables were created")
                
        except Exception as e:
            log.error(f"❌ Error verifying tables: {e}")
    
    def create_core_tables(self):
        """Create core tables using raw SQL."""
        log.info("Creating core tables...")
        
        try:
            # Create USER table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(30) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    login VARCHAR(100),
                    avatar_url TEXT,
                    location VARCHAR(100),
                    company VARCHAR(100),
                    bio TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create USER_GITHUB_CREDENTIALS table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER_GITHUB_CREDENTIALS" (
                    user_id UUID PRIMARY KEY REFERENCES "USER"(id) ON DELETE CASCADE,
                    github_access_token TEXT,
                    github_user_id VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create PROJECT table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    author_id UUID REFERENCES "USER"(id),
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    short_description TEXT,
                    image TEXT,
                    cover_images TEXT,
                    readme TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create PROJECT_EXTERNAL_LINK table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_EXTERNAL_LINK" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id) ON DELETE CASCADE,
                    type VARCHAR(50),
                    url TEXT NOT NULL
                )
            """))
            
            # Create TECH_STACK table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "TECH_STACK" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    icon_url TEXT,
                    type VARCHAR(20),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create TEAM_MEMBER table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "TEAM_MEMBER" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create PROJECT_ROLE table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_filled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create PROJECT_ROLE_APPLICATION table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_APPLICATION" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    project_title VARCHAR(100),
                    project_role_id UUID NOT NULL REFERENCES "PROJECT_ROLE"(id),
                    project_role_title VARCHAR(100),
                    project_description TEXT,
                    status VARCHAR(20),
                    motivation_letter TEXT,
                    rejection_reason TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create USER_SOCIAL_LINK table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER_SOCIAL_LINK" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    type VARCHAR(50),
                    url TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, type)
                )
            """))
            
            # Create CATEGORY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "CATEGORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create KEY_FEATURE table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "KEY_FEATURE" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id) ON DELETE CASCADE,
                    feature VARCHAR(200) NOT NULL
                )
            """))
            
            # Create PROJECT_GOAL table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_GOAL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id) ON DELETE CASCADE,
                    goal VARCHAR(200) NOT NULL
                )
            """))
            
            # Create association tables
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_TECH_STACK" (
                    project_id UUID REFERENCES "PROJECT"(id),
                    tech_stack_id UUID REFERENCES "TECH_STACK"(id),
                    PRIMARY KEY (project_id, tech_stack_id)
                )
            """))
            
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER_TECH_STACK" (
                    user_id UUID REFERENCES "USER"(id),
                    tech_stack_id UUID REFERENCES "TECH_STACK"(id),
                    PRIMARY KEY (user_id, tech_stack_id)
                )
            """))
            
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_CATEGORY" (
                    project_id UUID REFERENCES "PROJECT"(id),
                    category_id UUID REFERENCES "CATEGORY"(id),
                    PRIMARY KEY (project_id, category_id)
                )
            """))
            
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_TECH_STACK" (
                    project_role_id UUID REFERENCES "PROJECT_ROLE"(id),
                    tech_stack_id UUID REFERENCES "TECH_STACK"(id),
                    PRIMARY KEY (project_role_id, tech_stack_id)
                )
            """))
            
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "TEAM_MEMBER_PROJECT_ROLE" (
                    team_member_id UUID REFERENCES "TEAM_MEMBER"(id),
                    project_role_id UUID REFERENCES "PROJECT_ROLE"(id),
                    PRIMARY KEY (team_member_id, project_role_id)
                )
            """))
            
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_APPLICATION_KEY_FEATURE" (
                    application_id UUID REFERENCES "PROJECT_ROLE_APPLICATION"(id),
                    key_feature_id UUID REFERENCES "KEY_FEATURE"(id),
                    PRIMARY KEY (application_id, key_feature_id)
                )
            """))
            
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_APPLICATION_PROJECT_GOAL" (
                    application_id UUID REFERENCES "PROJECT_ROLE_APPLICATION"(id),
                    key_feature_id UUID REFERENCES "PROJECT_GOAL"(id),
                    PRIMARY KEY (application_id, key_feature_id)
                )
            """))
            
            self.db.commit()
            log.info("✅ Core tables created")
            
        except Exception as e:
            log.error(f"❌ Error creating core tables: {e}")
            self.db.rollback()
            raise


def main():
    """Run the complete table creation process."""
    log.info("🚀 Starting database table creation...")
    
    try:
        with TableCreator() as creator:
            # Create all tables using SQLAlchemy (recommended approach)
            creator.create_all_tables()
            
            # Alternative: Create tables manually if needed
            # creator.create_core_tables()
        
        log.info("🎉 Database table creation completed successfully!")
        log.info("📊 All tables are now ready for data population")
        
    except Exception as e:
        log.error(f"❌ Table creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 