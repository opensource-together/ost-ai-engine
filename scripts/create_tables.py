#!/usr/bin/env python3
"""
Database Table Creation Script

This script creates all database tables from the schema definition.
Uses classes for better organization and maintainability.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            "USER", "PROJECT", "PROJECT_training", "PROJECT_ROLE",
            "TEAM_MEMBER", "CONTRIBUTION", "APPLICATION",
            "SKILL_CATEGORY", "SKILL", "TECHNOLOGY", "DOMAIN_CATEGORY",
            "USER_SKILL", "USER_TECHNOLOGY", "PROJECT_SKILL",
            "PROJECT_TECHNOLOGY", "PROJECT_DOMAIN_CATEGORY",
            "PROJECT_ROLE_SKILL", "PROJECT_ROLE_TECHNOLOGY",
            "GOOD_FIRST_ISSUE", "ISSUE_SKILL", "ISSUE_TECHNOLOGY",
            "COMMUNITY_MEMBER", "LINKED_REPOSITORY"
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
        """Create core tables (USER, PROJECT, etc.) using raw SQL."""
        log.info("Creating core tables...")
        
        try:
            # Create USER table if not exists
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(30) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    bio TEXT,
                    github_username VARCHAR(39),
                    linkedin_url TEXT,
                    github_url TEXT,
                    portfolio_url TEXT,
                    contribution_score INTEGER DEFAULT 0,
                    level VARCHAR(20) DEFAULT 'beginner',
                    is_open_to_hire BOOLEAN DEFAULT FALSE,
                    location VARCHAR(100),
                    timezone VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create PROJECT table if not exists
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    owner_id UUID REFERENCES "USER"(id),
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    vision TEXT,
                    github_main_repo TEXT,
                    website_url TEXT,
                    documentation_url TEXT,
                    difficulty VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'active',
                    is_seeking_contributors BOOLEAN DEFAULT TRUE,
                    project_type VARCHAR(50),
                    license VARCHAR(50),
                    stars_count INTEGER DEFAULT 0,
                    contributors_count INTEGER DEFAULT 0,
                    language VARCHAR(50),
                    topics TEXT,
                    readme TEXT,
                    forks_count INTEGER,
                    open_issues_count INTEGER,
                    pushed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create PROJECT_training table if not exists
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_training" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    vision TEXT,
                    github_main_repo TEXT,
                    website_url TEXT,
                    difficulty VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'active',
                    is_seeking_contributors BOOLEAN DEFAULT TRUE,
                    project_type VARCHAR(50),
                    license VARCHAR(50),
                    stars_count INTEGER DEFAULT 0,
                    language VARCHAR(50),
                    topics TEXT,
                    readme TEXT,
                    forks_count INTEGER,
                    open_issues_count INTEGER,
                    pushed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            self.db.commit()
            log.info("✅ Core tables created")
            
        except Exception as e:
            log.error(f"❌ Error creating core tables: {e}")
            self.db.rollback()
            raise
    
    def create_entity_tables(self):
        """Create entity tables (SKILL, TECHNOLOGY, etc.) using raw SQL."""
        log.info("Creating entity tables...")
        
        try:
            # Create SKILL_CATEGORY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "SKILL_CATEGORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    icon_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create SKILL table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "SKILL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    skill_category_id UUID NOT NULL REFERENCES "SKILL_CATEGORY"(id),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    icon_url TEXT,
                    is_technical BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create TECHNOLOGY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    icon_url TEXT,
                    category VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create DOMAIN_CATEGORY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "DOMAIN_CATEGORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    icon_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            self.db.commit()
            log.info("✅ Entity tables created")
            
        except Exception as e:
            log.error(f"❌ Error creating entity tables: {e}")
            self.db.rollback()
            raise
    
    def create_relationship_tables(self):
        """Create relationship tables (USER_SKILL, PROJECT_TECHNOLOGY, etc.) using raw SQL."""
        log.info("Creating relationship tables...")
        
        try:
            # Create PROJECT_ROLE table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    responsibility_level VARCHAR(20),
                    time_commitment VARCHAR(20),
                    slots_available INTEGER DEFAULT 1,
                    slots_filled INTEGER DEFAULT 0,
                    experience_required VARCHAR(20),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create TEAM_MEMBER table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "TEAM_MEMBER" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    project_role_id UUID NOT NULL REFERENCES "PROJECT_ROLE"(id),
                    status VARCHAR(20) DEFAULT 'active',
                    contributions_count INTEGER DEFAULT 0,
                    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    left_at TIMESTAMP WITH TIME ZONE,
                    UNIQUE(user_id, project_id)
                )
            """))
            
            # Create CONTRIBUTION table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "CONTRIBUTION" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    issue_id UUID REFERENCES "GOOD_FIRST_ISSUE"(id),
                    type VARCHAR(50),
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    github_pr_url TEXT,
                    status VARCHAR(20) DEFAULT 'submitted',
                    reviewed_by UUID REFERENCES "USER"(id),
                    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    merged_at TIMESTAMP WITH TIME ZONE
                )
            """))
            
            # Create APPLICATION table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "APPLICATION" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    project_role_id UUID NOT NULL REFERENCES "PROJECT_ROLE"(id),
                    portfolio_links TEXT,
                    availability VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'pending',
                    reviewed_by UUID REFERENCES "USER"(id),
                    review_message TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    reviewed_at TIMESTAMP WITH TIME ZONE,
                    UNIQUE(user_id, project_role_id)
                )
            """))
            
            # Create USER_SKILL table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER_SKILL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    skill_id UUID NOT NULL REFERENCES "SKILL"(id),
                    proficiency_level VARCHAR(20) NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, skill_id)
                )
            """))
            
            # Create USER_TECHNOLOGY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "USER_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    proficiency_level VARCHAR(20) NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, technology_id)
                )
            """))
            
            # Create PROJECT_SKILL table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_SKILL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    skill_id UUID NOT NULL REFERENCES "SKILL"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(project_id, skill_id)
                )
            """))
            
            # Create PROJECT_TECHNOLOGY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(project_id, technology_id)
                )
            """))
            
            # Create PROJECT_DOMAIN_CATEGORY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_DOMAIN_CATEGORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    domain_category_id UUID NOT NULL REFERENCES "DOMAIN_CATEGORY"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(project_id, domain_category_id)
                )
            """))
            
            # Create PROJECT_ROLE_SKILL table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_SKILL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_role_id UUID NOT NULL REFERENCES "PROJECT_ROLE"(id),
                    skill_id UUID NOT NULL REFERENCES "SKILL"(id),
                    proficiency_level VARCHAR(20) NOT NULL,
                    is_required BOOLEAN DEFAULT TRUE,
                    UNIQUE(project_role_id, skill_id)
                )
            """))
            
            # Create PROJECT_ROLE_TECHNOLOGY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_role_id UUID NOT NULL REFERENCES "PROJECT_ROLE"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    proficiency_level VARCHAR(20) NOT NULL,
                    is_required BOOLEAN DEFAULT TRUE,
                    UNIQUE(project_role_id, technology_id)
                )
            """))
            
            # Create GOOD_FIRST_ISSUE table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "GOOD_FIRST_ISSUE" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    created_by UUID NOT NULL REFERENCES "USER"(id),
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    github_issue_url TEXT,
                    estimated_time VARCHAR(20),
                    difficulty VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'open',
                    assigned_to UUID REFERENCES "USER"(id),
                    is_ai_generated BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    completed_at TIMESTAMP WITH TIME ZONE
                )
            """))
            
            # Create ISSUE_SKILL table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "ISSUE_SKILL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    issue_id UUID NOT NULL REFERENCES "GOOD_FIRST_ISSUE"(id),
                    skill_id UUID NOT NULL REFERENCES "SKILL"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(issue_id, skill_id)
                )
            """))
            
            # Create ISSUE_TECHNOLOGY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "ISSUE_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    issue_id UUID NOT NULL REFERENCES "GOOD_FIRST_ISSUE"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(issue_id, technology_id)
                )
            """))
            
            # Create COMMUNITY_MEMBER table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "COMMUNITY_MEMBER" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    followed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    notifications_enabled BOOLEAN DEFAULT TRUE,
                    UNIQUE(user_id, project_id)
                )
            """))
            
            # Create LINKED_REPOSITORY table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS "LINKED_REPOSITORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    github_url TEXT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_main BOOLEAN DEFAULT FALSE,
                    language VARCHAR(50),
                    stars_count INTEGER DEFAULT 0,
                    last_sync TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(project_id, github_url)
                )
            """))
            
            self.db.commit()
            log.info("✅ Relationship tables created")
            
        except Exception as e:
            log.error(f"❌ Error creating relationship tables: {e}")
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
            # creator.create_entity_tables()
            # creator.create_relationship_tables()
        
        log.info("🎉 Database table creation completed successfully!")
        log.info("📊 All tables are now ready for data population")
        
    except Exception as e:
        log.error(f"❌ Table creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 