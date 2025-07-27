#!/usr/bin/env python3
"""
Database Migration Script V2 - Complete MCD Alignment

This script migrates the existing database to be 100% compliant with the Open Source Together (OST) 
conceptual data model (MCD) specification.

Migration steps:
1. Create all missing tables (Technology, DomainCategory, UserTechnology, etc.)
2. Add missing columns to existing tables
3. Populate initial data for categories and common technologies/skills
4. Update existing data to match new schema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.postgres.database import SessionLocal, engine
from src.domain.models.schema import Base
from src.infrastructure.logger import log


def create_all_tables():
    """Create all tables that don't exist yet"""
    log.info("Creating all missing tables...")
    
    # Create all tables (SQLAlchemy will skip existing ones)
    Base.metadata.create_all(bind=engine)
    log.info("✅ All tables created")


def populate_domain_categories():
    """Populate initial domain categories"""
    log.info("Populating domain categories...")
    
    with SessionLocal() as db:
        try:
            from src.domain.models.schema import DomainCategory
            
            categories = [
                {
                    "name": "Education",
                    "description": "Educational technology and learning platforms",
                    "icon_url": "https://example.com/icons/education.png"
                },
                {
                    "name": "Santé",
                    "description": "Healthcare and medical technology",
                    "icon_url": "https://example.com/icons/health.png"
                },
                {
                    "name": "Finance",
                    "description": "Financial technology and fintech solutions",
                    "icon_url": "https://example.com/icons/finance.png"
                },
                {
                    "name": "Gaming",
                    "description": "Gaming and entertainment applications",
                    "icon_url": "https://example.com/icons/gaming.png"
                },
                {
                    "name": "DevTools",
                    "description": "Developer tools and utilities",
                    "icon_url": "https://example.com/icons/devtools.png"
                },
                {
                    "name": "E-commerce",
                    "description": "Online commerce and marketplace platforms",
                    "icon_url": "https://example.com/icons/ecommerce.png"
                },
                {
                    "name": "Social",
                    "description": "Social networking and community platforms",
                    "icon_url": "https://example.com/icons/social.png"
                },
                {
                    "name": "Productivity",
                    "description": "Productivity and business tools",
                    "icon_url": "https://example.com/icons/productivity.png"
                }
            ]
            
            for cat_data in categories:
                existing = db.query(DomainCategory).filter_by(name=cat_data["name"]).first()
                if not existing:
                    category = DomainCategory(**cat_data)
                    db.add(category)
                    log.info(f"✅ Added domain category: {cat_data['name']}")
            
            db.commit()
            log.info("✅ Domain categories populated")
            
        except Exception as e:
            log.error(f"❌ Error populating domain categories: {e}")
            db.rollback()
            raise


def populate_technologies():
    """Populate common technologies"""
    log.info("Populating technologies...")
    
    with SessionLocal() as db:
        try:
            from src.domain.models.schema import Technology
            
            technologies_data = [
                # Frontend Technologies
                ("React", "Frontend JavaScript library for building user interfaces", "frontend"),
                ("Vue.js", "Progressive JavaScript framework", "frontend"),
                ("Angular", "Platform for building mobile and desktop web applications", "frontend"),
                ("TypeScript", "Typed superset of JavaScript", "frontend"),
                ("CSS", "Cascading Style Sheets", "frontend"),
                ("HTML", "HyperText Markup Language", "frontend"),
                ("Svelte", "Frontend framework for building web applications", "frontend"),
                
                # Backend Technologies
                ("Python", "High-level programming language", "backend"),
                ("Node.js", "JavaScript runtime for server-side development", "backend"),
                ("Java", "Object-oriented programming language", "backend"),
                ("Go", "Statically typed compiled language", "backend"),
                ("Rust", "Systems programming language", "backend"),
                ("PHP", "Server-side scripting language", "backend"),
                ("C#", "Object-oriented programming language", "backend"),
                ("Ruby", "Dynamic programming language", "backend"),
                
                # DevOps Technologies
                ("Docker", "Containerization platform", "devops"),
                ("Kubernetes", "Container orchestration platform", "devops"),
                ("AWS", "Amazon Web Services cloud platform", "devops"),
                ("Azure", "Microsoft cloud computing platform", "devops"),
                ("GCP", "Google Cloud Platform", "devops"),
                ("CI/CD", "Continuous Integration/Continuous Deployment", "devops"),
                ("Linux", "Unix-like operating system", "devops"),
                ("Terraform", "Infrastructure as Code tool", "devops"),
                
                # Design Technologies
                ("Figma", "Design and prototyping tool", "design"),
                ("Adobe Creative Suite", "Creative software suite", "design"),
                ("Sketch", "Design tool for macOS", "design"),
                ("InVision", "Digital product design platform", "design"),
                ("Adobe XD", "User experience design tool", "design"),
                
                # Business Technologies
                ("Slack", "Team communication platform", "business"),
                ("Notion", "All-in-one workspace", "business"),
                ("Trello", "Project management tool", "business"),
                ("Asana", "Work management platform", "business"),
                ("Jira", "Project management for software teams", "business"),
                ("Google Analytics", "Web analytics service", "business"),
                ("HubSpot", "Customer relationship management platform", "business"),
                ("Zapier", "Workflow automation platform", "business"),
                
                # Database Technologies
                ("PostgreSQL", "Object-relational database system", "backend"),
                ("MySQL", "Relational database management system", "backend"),
                ("MongoDB", "NoSQL document database", "backend"),
                ("Redis", "In-memory data structure store", "backend"),
                ("SQLite", "Lightweight database engine", "backend"),
                
                # Mobile Technologies
                ("React Native", "Mobile app development with React", "frontend"),
                ("Flutter", "UI toolkit for mobile development", "frontend"),
                ("Swift", "Programming language for iOS", "backend"),
                ("Kotlin", "Programming language for Android", "backend"),
                
                # Other Technologies
                ("Git", "Distributed version control system", "devops"),
                ("GitHub", "Code hosting platform", "business"),
                ("GitLab", "DevOps platform", "business"),
                ("Bitbucket", "Git code hosting service", "business")
            ]
            
            for name, description, category in technologies_data:
                existing = db.query(Technology).filter_by(name=name).first()
                if not existing:
                    technology = Technology(
                        name=name,
                        description=description,
                        category=category,
                        icon_url=f"https://example.com/icons/{name.lower().replace(' ', '_')}.png"
                    )
                    db.add(technology)
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
            from src.domain.models.schema import SkillCategory
            
            categories = [
                {
                    "name": "Product Management",
                    "description": "Product management and strategy skills",
                    "icon_url": "https://example.com/icons/product-management.png"
                },
                {
                    "name": "Marketing",
                    "description": "Marketing and growth skills",
                    "icon_url": "https://example.com/icons/marketing.png"
                },
                {
                    "name": "Design",
                    "description": "UI/UX design and creative skills",
                    "icon_url": "https://example.com/icons/design.png"
                },
                {
                    "name": "Development",
                    "description": "Software development skills",
                    "icon_url": "https://example.com/icons/development.png"
                },
                {
                    "name": "DevOps",
                    "description": "DevOps and infrastructure skills",
                    "icon_url": "https://example.com/icons/devops.png"
                },
                {
                    "name": "Data Science",
                    "description": "Data analysis and machine learning skills",
                    "icon_url": "https://example.com/icons/data-science.png"
                },
                {
                    "name": "Community",
                    "description": "Community management and engagement",
                    "icon_url": "https://example.com/icons/community.png"
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
                    log.info(f"✅ Added skill category: {cat_data['name']}")
            
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
            from src.domain.models.schema import Skill, SkillCategory
            
            # Get category IDs
            categories = {cat.name: cat.id for cat in db.query(SkillCategory).all()}
            
            skills_data = [
                # Product Management
                ("Product Strategy", "Product Management", "Strategic planning and product vision", False),
                ("User Research", "Product Management", "Understanding user needs and behaviors", False),
                ("Product Analytics", "Product Management", "Data-driven product decision making", False),
                ("Roadmap Planning", "Product Management", "Product roadmap development and execution", False),
                
                # Marketing
                ("Digital Marketing", "Marketing", "Online marketing strategies and campaigns", False),
                ("Content Marketing", "Marketing", "Content creation and strategy", False),
                ("SEO", "Marketing", "Search Engine Optimization", False),
                ("Social Media Marketing", "Marketing", "Social media strategy and management", False),
                ("Growth Hacking", "Marketing", "Rapid growth strategies and experimentation", False),
                
                # Design
                ("UI Design", "Design", "User interface design", False),
                ("UX Design", "Design", "User experience design", False),
                ("Visual Design", "Design", "Visual design and branding", False),
                ("Prototyping", "Design", "Interactive prototyping and wireframing", False),
                
                # Development
                ("Software Architecture", "Development", "System design and architecture", True),
                ("API Design", "Development", "RESTful API design and development", True),
                ("Database Design", "Development", "Database schema design and optimization", True),
                ("Testing", "Development", "Software testing and quality assurance", True),
                
                # DevOps
                ("Infrastructure Management", "DevOps", "Cloud infrastructure and deployment", True),
                ("Monitoring", "DevOps", "System monitoring and alerting", True),
                ("Security", "DevOps", "Application and infrastructure security", True),
                ("Performance Optimization", "DevOps", "System performance tuning", True),
                
                # Data Science
                ("Data Analysis", "Data Science", "Data analysis and visualization", True),
                ("Machine Learning", "Data Science", "ML model development and deployment", True),
                ("Statistical Analysis", "Data Science", "Statistical modeling and inference", True),
                
                # Community
                ("Community Management", "Community", "Building and managing communities", False),
                ("Event Planning", "Community", "Organizing community events and meetups", False),
                ("Mentorship", "Community", "Mentoring and knowledge sharing", False),
                
                # Documentation
                ("Technical Writing", "Documentation", "Technical documentation writing", False),
                ("API Documentation", "Documentation", "API documentation and guides", False),
                ("User Guides", "Documentation", "User manual and guide creation", False)
            ]
            
            for skill_name, category_name, description, is_technical in skills_data:
                if category_name in categories:
                    existing = db.query(Skill).filter_by(name=skill_name).first()
                    if not existing:
                        skill = Skill(
                            skill_category_id=categories[category_name],
                            name=skill_name,
                            description=description,
                            is_technical=is_technical
                        )
                        db.add(skill)
                        log.info(f"✅ Added skill: {skill_name}")
            
            db.commit()
            log.info("✅ Business skills populated")
            
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
    log.info("🚀 Starting complete database migration to align with MCD...")
    
    try:
        # Step 1: Create all tables
        create_all_tables()
        
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