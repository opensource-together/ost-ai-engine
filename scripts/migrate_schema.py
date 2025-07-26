#!/usr/bin/env python3
"""
Database Migration Script - Align with MCD Specification

This script migrates the existing database to align with the Open Source Together (OST) 
conceptual data model (MCD) specification.

Migration steps:
1. Add new columns to existing tables
2. Create new tables for skills, issues, and repositories
3. Populate initial data for skill categories and common skills
4. Update existing data to match new schema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.postgres.database import SessionLocal, engine
from src.domain.models.schema import Base
from src.infrastructure.logger import log


def create_new_tables():
    """Create new tables that don't exist yet"""
    log.info("Creating new tables...")
    
    # Create all tables (SQLAlchemy will skip existing ones)
    Base.metadata.create_all(bind=engine)
    log.info("✅ New tables created")


def add_user_columns():
    """Add new columns to USER table"""
    log.info("Adding new columns to USER table...")
    
    with SessionLocal() as db:
        try:
            # Add new columns to USER table
            columns_to_add = [
                "bio TEXT",
                "github_username VARCHAR(39)",
                "linkedin_url TEXT",
                "github_url TEXT", 
                "portfolio_url TEXT",
                "contribution_score INTEGER DEFAULT 0",
                "level VARCHAR(20) DEFAULT 'beginner'",
                "is_open_to_hire BOOLEAN DEFAULT FALSE",
                "location VARCHAR(100)",
                "timezone VARCHAR(50)"
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    db.execute(text(f'ALTER TABLE "USER" ADD COLUMN IF NOT EXISTS {column_def}'))
                    log.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    log.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            db.commit()
            log.info("✅ USER table updated")
            
        except Exception as e:
            log.error(f"❌ Error updating USER table: {e}")
            db.rollback()
            raise


def add_project_columns():
    """Add new columns to PROJECT table"""
    log.info("Adding new columns to PROJECT table...")
    
    with SessionLocal() as db:
        try:
            # Add new columns to PROJECT table
            columns_to_add = [
                "owner_id UUID REFERENCES \"USER\"(id)",
                "documentation_url TEXT",
                "contributors_count INTEGER DEFAULT 0"
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    db.execute(text(f'ALTER TABLE "PROJECT" ADD COLUMN IF NOT EXISTS {column_def}'))
                    log.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    log.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            db.commit()
            log.info("✅ PROJECT table updated")
            
        except Exception as e:
            log.error(f"❌ Error updating PROJECT table: {e}")
            db.rollback()
            raise


def add_project_role_columns():
    """Add new columns to PROJECT_ROLE table"""
    log.info("Adding new columns to PROJECT_ROLE table...")
    
    with SessionLocal() as db:
        try:
            columns_to_add = [
                "responsibility_level VARCHAR(20)",
                "time_commitment VARCHAR(20)",
                "slots_available INTEGER DEFAULT 1",
                "slots_filled INTEGER DEFAULT 0",
                "experience_required VARCHAR(20)"
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    db.execute(text(f'ALTER TABLE "PROJECT_ROLE" ADD COLUMN IF NOT EXISTS {column_def}'))
                    log.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    log.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            db.commit()
            log.info("✅ PROJECT_ROLE table updated")
            
        except Exception as e:
            log.error(f"❌ Error updating PROJECT_ROLE table: {e}")
            db.rollback()
            raise


def add_team_member_columns():
    """Add new columns to TEAM_MEMBER table"""
    log.info("Adding new columns to TEAM_MEMBER table...")
    
    with SessionLocal() as db:
        try:
            columns_to_add = [
                "project_role_id UUID REFERENCES \"PROJECT_ROLE\"(id)",
                "status VARCHAR(20) DEFAULT 'active'",
                "contributions_count INTEGER DEFAULT 0",
                "left_at TIMESTAMP WITH TIME ZONE"
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    db.execute(text(f'ALTER TABLE "TEAM_MEMBER" ADD COLUMN IF NOT EXISTS {column_def}'))
                    log.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    log.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            db.commit()
            log.info("✅ TEAM_MEMBER table updated")
            
        except Exception as e:
            log.error(f"❌ Error updating TEAM_MEMBER table: {e}")
            db.rollback()
            raise


def add_contribution_columns():
    """Add new columns to CONTRIBUTION table"""
    log.info("Adding new columns to CONTRIBUTION table...")
    
    with SessionLocal() as db:
        try:
            columns_to_add = [
                "issue_id UUID REFERENCES \"GOOD_FIRST_ISSUE\"(id)",
                "description TEXT",
                "github_pr_url TEXT",
                "status VARCHAR(20) DEFAULT 'submitted'",
                "reviewed_by UUID REFERENCES \"USER\"(id)",
                "merged_at TIMESTAMP WITH TIME ZONE"
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    db.execute(text(f'ALTER TABLE "CONTRIBUTION" ADD COLUMN IF NOT EXISTS {column_def}'))
                    log.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    log.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            db.commit()
            log.info("✅ CONTRIBUTION table updated")
            
        except Exception as e:
            log.error(f"❌ Error updating CONTRIBUTION table: {e}")
            db.rollback()
            raise


def add_application_columns():
    """Add new columns to APPLICATION table"""
    log.info("Adding new columns to APPLICATION table...")
    
    with SessionLocal() as db:
        try:
            columns_to_add = [
                "portfolio_links TEXT",
                "availability VARCHAR(20)",
                "reviewed_by UUID REFERENCES \"USER\"(id)",
                "review_message TEXT",
                "reviewed_at TIMESTAMP WITH TIME ZONE"
            ]
            
            for column_def in columns_to_add:
                column_name = column_def.split()[0]
                try:
                    db.execute(text(f'ALTER TABLE "APPLICATION" ADD COLUMN IF NOT EXISTS {column_def}'))
                    log.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    log.warning(f"⚠️ Column {column_name} might already exist: {e}")
            
            db.commit()
            log.info("✅ APPLICATION table updated")
            
        except Exception as e:
            log.error(f"❌ Error updating APPLICATION table: {e}")
            db.rollback()
            raise


def populate_skill_categories():
    """Populate initial skill categories"""
    log.info("Populating skill categories...")
    
    with SessionLocal() as db:
        try:
            from src.domain.models.schema import SkillCategory
            
            categories = [
                {
                    "name": "Frontend",
                    "description": "Frontend development technologies and frameworks",
                    "icon_url": "https://example.com/icons/frontend.png"
                },
                {
                    "name": "Backend", 
                    "description": "Backend development technologies and frameworks",
                    "icon_url": "https://example.com/icons/backend.png"
                },
                {
                    "name": "Design",
                    "description": "UI/UX design and creative skills",
                    "icon_url": "https://example.com/icons/design.png"
                },
                {
                    "name": "DevOps",
                    "description": "DevOps, infrastructure, and deployment",
                    "icon_url": "https://example.com/icons/devops.png"
                },
                {
                    "name": "Data Science",
                    "description": "Data analysis, machine learning, and AI",
                    "icon_url": "https://example.com/icons/data-science.png"
                },
                {
                    "name": "Mobile",
                    "description": "Mobile app development",
                    "icon_url": "https://example.com/icons/mobile.png"
                },
                {
                    "name": "Marketing",
                    "description": "Marketing, SEO, and community management",
                    "icon_url": "https://example.com/icons/marketing.png"
                },
                {
                    "name": "Documentation",
                    "description": "Technical writing and documentation",
                    "icon_url": "https://example.com/icons/documentation.png"
                }
            ]
            
            for cat_data in categories:
                existing = db.query(SkillCategory).filter_by(name=cat_data["name"]).first()
                if not existing:
                    category = SkillCategory(**cat_data)
                    db.add(category)
                    log.info(f"✅ Added category: {cat_data['name']}")
            
            db.commit()
            log.info("✅ Skill categories populated")
            
        except Exception as e:
            log.error(f"❌ Error populating skill categories: {e}")
            db.rollback()
            raise


def populate_common_skills():
    """Populate common skills"""
    log.info("Populating common skills...")
    
    with SessionLocal() as db:
        try:
            from src.domain.models.schema import Skill, SkillCategory
            
            # Get category IDs
            categories = {cat.name: cat.id for cat in db.query(SkillCategory).all()}
            
            skills_data = [
                # Frontend
                ("React", "Frontend", "React.js library for building user interfaces"),
                ("Vue.js", "Frontend", "Progressive JavaScript framework"),
                ("Angular", "Frontend", "Platform for building mobile and desktop web applications"),
                ("TypeScript", "Frontend", "Typed superset of JavaScript"),
                ("CSS", "Frontend", "Cascading Style Sheets"),
                ("HTML", "Frontend", "HyperText Markup Language"),
                
                # Backend
                ("Python", "Backend", "High-level programming language"),
                ("Node.js", "Backend", "JavaScript runtime for server-side development"),
                ("Java", "Backend", "Object-oriented programming language"),
                ("Go", "Backend", "Statically typed compiled language"),
                ("Rust", "Backend", "Systems programming language"),
                ("PHP", "Backend", "Server-side scripting language"),
                
                # DevOps
                ("Docker", "DevOps", "Containerization platform"),
                ("Kubernetes", "DevOps", "Container orchestration platform"),
                ("AWS", "DevOps", "Amazon Web Services cloud platform"),
                ("CI/CD", "DevOps", "Continuous Integration/Continuous Deployment"),
                ("Linux", "DevOps", "Unix-like operating system"),
                
                # Design
                ("UI Design", "Design", "User interface design"),
                ("UX Design", "Design", "User experience design"),
                ("Figma", "Design", "Design and prototyping tool"),
                ("Adobe Creative Suite", "Design", "Creative software suite"),
                
                # Data Science
                ("Machine Learning", "Data Science", "Machine learning algorithms and models"),
                ("Data Analysis", "Data Science", "Data analysis and visualization"),
                ("SQL", "Data Science", "Structured Query Language"),
                ("Pandas", "Data Science", "Data manipulation library"),
                
                # Mobile
                ("React Native", "Mobile", "Mobile app development with React"),
                ("Flutter", "Mobile", "UI toolkit for mobile development"),
                ("iOS Development", "Mobile", "Apple mobile development"),
                ("Android Development", "Mobile", "Google mobile development"),
                
                # Marketing
                ("SEO", "Marketing", "Search Engine Optimization"),
                ("Content Marketing", "Marketing", "Content creation and strategy"),
                ("Social Media", "Marketing", "Social media management"),
                ("Community Management", "Marketing", "Building and managing communities"),
                
                # Documentation
                ("Technical Writing", "Documentation", "Technical documentation writing"),
                ("API Documentation", "Documentation", "API documentation and guides"),
                ("User Guides", "Documentation", "User manual and guide creation")
            ]
            
            for skill_name, category_name, description in skills_data:
                if category_name in categories:
                    existing = db.query(Skill).filter_by(name=skill_name).first()
                    if not existing:
                        skill = Skill(
                            skill_category_id=categories[category_name],
                            name=skill_name,
                            description=description,
                            is_technical=category_name not in ["Design", "Marketing", "Documentation"]
                        )
                        db.add(skill)
                        log.info(f"✅ Added skill: {skill_name}")
            
            db.commit()
            log.info("✅ Common skills populated")
            
        except Exception as e:
            log.error(f"❌ Error populating skills: {e}")
            db.rollback()
            raise


def update_existing_data():
    """Update existing data to match new schema"""
    log.info("Updating existing data...")
    
    with SessionLocal() as db:
        try:
            # Set default owner_id for existing projects (use first user)
            db.execute(text('''
                UPDATE "PROJECT" 
                SET owner_id = (SELECT id FROM "USER" LIMIT 1)
                WHERE owner_id IS NULL
            '''))
            log.info("✅ Set default project owners")
            
            # Update project_type values to match new enum
            db.execute(text('''
                UPDATE "PROJECT" 
                SET project_type = 'application'
                WHERE project_type IN ('web_app', 'api', 'mobile_app')
            '''))
            log.info("✅ Updated project types")
            
            db.commit()
            log.info("✅ Existing data updated")
            
        except Exception as e:
            log.error(f"❌ Error updating existing data: {e}")
            db.rollback()
            raise


def main():
    """Run the complete migration"""
    log.info("🚀 Starting database migration to align with MCD...")
    
    try:
        # Step 1: Create new tables
        create_new_tables()
        
        # Step 2: Add columns to existing tables
        add_user_columns()
        add_project_columns()
        add_project_role_columns()
        add_team_member_columns()
        add_contribution_columns()
        add_application_columns()
        
        # Step 3: Populate initial data
        populate_skill_categories()
        populate_common_skills()
        
        # Step 4: Update existing data
        update_existing_data()
        
        log.info("🎉 Database migration completed successfully!")
        log.info("📊 Schema now aligned with Open Source Together MCD specification")
        
    except Exception as e:
        log.error(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 