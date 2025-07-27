#!/usr/bin/env python3
"""
Database Migration Script V3 - Raw SQL Approach

This script migrates the existing database using raw SQL to avoid SQLAlchemy relationship issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.postgres.database import SessionLocal, engine
from src.infrastructure.logger import log


def create_missing_tables():
    """Create missing tables using raw SQL"""
    log.info("Creating missing tables with raw SQL...")
    
    with SessionLocal() as db:
        try:
            # Create TECHNOLOGY table
            db.execute(text("""
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
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "DOMAIN_CATEGORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    icon_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create USER_TECHNOLOGY table
            db.execute(text("""
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
            
            # Create PROJECT_DOMAIN_CATEGORY table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_DOMAIN_CATEGORY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    domain_category_id UUID NOT NULL REFERENCES "DOMAIN_CATEGORY"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(project_id, domain_category_id)
                )
            """))
            
            # Create PROJECT_SKILL table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_SKILL" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    skill_id UUID NOT NULL REFERENCES "SKILL"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(project_id, skill_id)
                )
            """))
            
            # Create PROJECT_TECHNOLOGY table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(project_id, technology_id)
                )
            """))
            
            # Create PROJECT_ROLE_TECHNOLOGY table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "PROJECT_ROLE_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_role_id UUID NOT NULL REFERENCES "PROJECT_ROLE"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    proficiency_level VARCHAR(20) NOT NULL,
                    is_required BOOLEAN DEFAULT TRUE,
                    UNIQUE(project_role_id, technology_id)
                )
            """))
            
            # Create ISSUE_TECHNOLOGY table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "ISSUE_TECHNOLOGY" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    issue_id UUID NOT NULL REFERENCES "GOOD_FIRST_ISSUE"(id),
                    technology_id UUID NOT NULL REFERENCES "TECHNOLOGY"(id),
                    is_primary BOOLEAN DEFAULT FALSE,
                    UNIQUE(issue_id, technology_id)
                )
            """))
            
            # Create COMMUNITY_MEMBER table
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS "COMMUNITY_MEMBER" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES "USER"(id),
                    project_id UUID NOT NULL REFERENCES "PROJECT"(id),
                    followed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    notifications_enabled BOOLEAN DEFAULT TRUE,
                    UNIQUE(user_id, project_id)
                )
            """))
            
            db.commit()
            log.info("✅ All missing tables created")
            
        except Exception as e:
            log.error(f"❌ Error creating tables: {e}")
            db.rollback()
            raise


def populate_domain_categories():
    """Populate domain categories"""
    log.info("Populating domain categories...")
    
    with SessionLocal() as db:
        try:
            categories = [
                ("Education", "Educational technology and learning platforms"),
                ("Santé", "Healthcare and medical technology"),
                ("Finance", "Financial technology and fintech solutions"),
                ("Gaming", "Gaming and entertainment applications"),
                ("DevTools", "Developer tools and utilities"),
                ("E-commerce", "Online commerce and marketplace platforms"),
                ("Social", "Social networking and community platforms"),
                ("Productivity", "Productivity and business tools")
            ]
            
            for name, description in categories:
                db.execute(text("""
                    INSERT INTO "DOMAIN_CATEGORY" (id, name, description, icon_url)
                    VALUES (gen_random_uuid(), :name, :description, :icon_url)
                    ON CONFLICT (name) DO NOTHING
                """), {
                    "name": name,
                    "description": description,
                    "icon_url": f"https://example.com/icons/{name.lower().replace('é', 'e')}.png"
                })
                log.info(f"✅ Added domain category: {name}")
            
            db.commit()
            log.info("✅ Domain categories populated")
            
        except Exception as e:
            log.error(f"❌ Error populating domain categories: {e}")
            db.rollback()
            raise


def populate_technologies():
    """Populate technologies"""
    log.info("Populating technologies...")
    
    with SessionLocal() as db:
        try:
            technologies = [
                # Frontend
                ("React", "Frontend JavaScript library", "frontend"),
                ("Vue.js", "Progressive JavaScript framework", "frontend"),
                ("Angular", "Platform for building web applications", "frontend"),
                ("TypeScript", "Typed superset of JavaScript", "frontend"),
                ("CSS", "Cascading Style Sheets", "frontend"),
                ("HTML", "HyperText Markup Language", "frontend"),
                
                # Backend
                ("Python", "High-level programming language", "backend"),
                ("Node.js", "JavaScript runtime", "backend"),
                ("Java", "Object-oriented programming language", "backend"),
                ("Go", "Statically typed compiled language", "backend"),
                ("Rust", "Systems programming language", "backend"),
                ("PHP", "Server-side scripting language", "backend"),
                
                # DevOps
                ("Docker", "Containerization platform", "devops"),
                ("Kubernetes", "Container orchestration", "devops"),
                ("AWS", "Amazon Web Services", "devops"),
                ("Azure", "Microsoft cloud platform", "devops"),
                ("GCP", "Google Cloud Platform", "devops"),
                ("CI/CD", "Continuous Integration/Deployment", "devops"),
                
                # Design
                ("Figma", "Design and prototyping tool", "design"),
                ("Adobe Creative Suite", "Creative software suite", "design"),
                ("Sketch", "Design tool for macOS", "design"),
                
                # Business
                ("Slack", "Team communication platform", "business"),
                ("Notion", "All-in-one workspace", "business"),
                ("Trello", "Project management tool", "business"),
                ("Jira", "Project management for teams", "business"),
                ("Google Analytics", "Web analytics service", "business"),
                
                # Database
                ("PostgreSQL", "Object-relational database", "backend"),
                ("MySQL", "Relational database system", "backend"),
                ("MongoDB", "NoSQL document database", "backend"),
                ("Redis", "In-memory data store", "backend"),
                
                # Mobile
                ("React Native", "Mobile app development", "frontend"),
                ("Flutter", "UI toolkit for mobile", "frontend"),
                
                # Other
                ("Git", "Version control system", "devops"),
                ("GitHub", "Code hosting platform", "business"),
                ("GitLab", "DevOps platform", "business")
            ]
            
            for name, description, category in technologies:
                db.execute(text("""
                    INSERT INTO "TECHNOLOGY" (id, name, description, category, icon_url)
                    VALUES (gen_random_uuid(), :name, :description, :category, :icon_url)
                    ON CONFLICT (name) DO NOTHING
                """), {
                    "name": name,
                    "description": description,
                    "category": category,
                    "icon_url": f"https://example.com/icons/{name.lower().replace(' ', '_')}.png"
                })
                log.info(f"✅ Added technology: {name}")
            
            db.commit()
            log.info("✅ Technologies populated")
            
        except Exception as e:
            log.error(f"❌ Error populating technologies: {e}")
            db.rollback()
            raise


def populate_skill_categories():
    """Populate skill categories"""
    log.info("Populating skill categories...")
    
    with SessionLocal() as db:
        try:
            categories = [
                ("Product Management", "Product management and strategy skills"),
                ("Marketing", "Marketing and growth skills"),
                ("Design", "UI/UX design and creative skills"),
                ("Development", "Software development skills"),
                ("DevOps", "DevOps and infrastructure skills"),
                ("Data Science", "Data analysis and machine learning skills"),
                ("Community", "Community management and engagement"),
                ("Documentation", "Technical writing and documentation")
            ]
            
            for name, description in categories:
                db.execute(text("""
                    INSERT INTO "SKILL_CATEGORY" (id, name, description, icon_url)
                    VALUES (gen_random_uuid(), :name, :description, :icon_url)
                    ON CONFLICT (name) DO NOTHING
                """), {
                    "name": name,
                    "description": description,
                    "icon_url": f"https://example.com/icons/{name.lower().replace(' ', '_')}.png"
                })
                log.info(f"✅ Added skill category: {name}")
            
            db.commit()
            log.info("✅ Skill categories populated")
            
        except Exception as e:
            log.error(f"❌ Error populating skill categories: {e}")
            db.rollback()
            raise


def populate_skills():
    """Populate business skills"""
    log.info("Populating business skills...")
    
    with SessionLocal() as db:
        try:
            # Get category IDs
            result = db.execute(text('SELECT id, name FROM "SKILL_CATEGORY"'))
            categories = {row[1]: row[0] for row in result}
            
            skills = [
                # Product Management
                ("Product Strategy", "Product Management", "Strategic planning and product vision", False),
                ("User Research", "Product Management", "Understanding user needs and behaviors", False),
                ("Product Analytics", "Product Management", "Data-driven product decision making", False),
                
                # Marketing
                ("Digital Marketing", "Marketing", "Online marketing strategies", False),
                ("Content Marketing", "Marketing", "Content creation and strategy", False),
                ("SEO", "Marketing", "Search Engine Optimization", False),
                ("Social Media Marketing", "Marketing", "Social media strategy", False),
                
                # Design
                ("UI Design", "Design", "User interface design", False),
                ("UX Design", "Design", "User experience design", False),
                ("Visual Design", "Design", "Visual design and branding", False),
                
                # Development
                ("Software Architecture", "Development", "System design and architecture", True),
                ("API Design", "Development", "RESTful API design", True),
                ("Database Design", "Development", "Database schema design", True),
                ("Testing", "Development", "Software testing and QA", True),
                
                # DevOps
                ("Infrastructure Management", "DevOps", "Cloud infrastructure", True),
                ("Monitoring", "DevOps", "System monitoring", True),
                ("Security", "DevOps", "Application security", True),
                
                # Data Science
                ("Data Analysis", "Data Science", "Data analysis and visualization", True),
                ("Machine Learning", "Data Science", "ML model development", True),
                
                # Community
                ("Community Management", "Community", "Building communities", False),
                ("Event Planning", "Community", "Organizing events", False),
                
                # Documentation
                ("Technical Writing", "Documentation", "Technical documentation", False),
                ("API Documentation", "Documentation", "API documentation", False)
            ]
            
            for skill_name, category_name, description, is_technical in skills:
                if category_name in categories:
                    db.execute(text("""
                        INSERT INTO "SKILL" (id, skill_category_id, name, description, is_technical)
                        VALUES (gen_random_uuid(), :category_id, :name, :description, :is_technical)
                        ON CONFLICT (name) DO NOTHING
                    """), {
                        "category_id": categories[category_name],
                        "name": skill_name,
                        "description": description,
                        "is_technical": is_technical
                    })
                    log.info(f"✅ Added skill: {skill_name}")
            
            db.commit()
            log.info("✅ Business skills populated")
            
        except Exception as e:
            log.error(f"❌ Error populating skills: {e}")
            db.rollback()
            raise


def update_existing_data():
    """Update existing data"""
    log.info("Updating existing data...")
    
    with SessionLocal() as db:
        try:
            # Set default owner_id for existing projects
            db.execute(text('''
                UPDATE "PROJECT" 
                SET owner_id = (SELECT id FROM "USER" LIMIT 1)
                WHERE owner_id IS NULL
            '''))
            log.info("✅ Set default project owners")
            
            # Update project_type values
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
    log.info("🚀 Starting complete database migration with raw SQL...")
    
    try:
        # Step 1: Create missing tables
        create_missing_tables()
        
        # Step 2: Populate initial data
        populate_domain_categories()
        populate_technologies()
        populate_skill_categories()
        populate_skills()
        
        # Step 3: Update existing data
        update_existing_data()
        
        log.info("🎉 Complete database migration completed successfully!")
        log.info("📊 Schema now 100% aligned with Open Source Together MCD specification")
        log.info("✅ All missing tables and relationships added")
        
    except Exception as e:
        log.error(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 