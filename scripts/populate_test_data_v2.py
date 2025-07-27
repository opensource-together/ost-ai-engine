#!/usr/bin/env python3
"""
Populate Test Data Script V2 - Complete User Interactions

This script populates the database with test data for all user interactions
including the new Technology and UserTechnology tables.
"""

import sys
import os
import random
import uuid
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.postgres.database import SessionLocal
from src.infrastructure.logger import log


def populate_user_technologies_sql(db):
    """Add technologies to users using raw SQL"""
    log.info("Adding technologies to users using SQL...")
    
    # Get user IDs
    users_result = db.execute(text('SELECT id FROM "USER" LIMIT 10'))
    user_ids = [row[0] for row in users_result]
    
    if not user_ids:
        log.warning("No users found")
        return
    
    # Get technology IDs
    technologies_result = db.execute(text('SELECT id FROM "TECHNOLOGY"'))
    technology_ids = [row[0] for row in technologies_result]
    
    if not technology_ids:
        log.warning("No technologies found")
        return
    
    # Add technologies to users
    proficiency_levels = ["learning", "basic", "intermediate", "advanced", "expert"]
    
    for user_id in user_ids:
        # Add 3-6 random technologies per user
        user_technologies_count = random.randint(3, 6)
        user_technologies = random.sample(technology_ids, min(user_technologies_count, len(technology_ids)))
        
        for technology_id in user_technologies:
            # Check if user already has this technology
            existing = db.execute(text(
                'SELECT id FROM "USER_TECHNOLOGY" WHERE user_id = :user_id AND technology_id = :technology_id'
            ), {"user_id": user_id, "technology_id": technology_id}).fetchone()
            
            if not existing:
                user_technology_sql = """
                INSERT INTO "USER_TECHNOLOGY" (id, user_id, technology_id, proficiency_level, is_primary, created_at)
                VALUES (gen_random_uuid(), :user_id, :technology_id, :proficiency, :is_primary, NOW())
                """
                
                db.execute(text(user_technology_sql), {
                    "user_id": user_id,
                    "technology_id": technology_id,
                    "proficiency": random.choice(proficiency_levels),
                    "is_primary": random.choice([True, False])
                })
                log.info(f"✅ Added technology to user {user_id}")
    
    db.commit()
    log.info("✅ User technologies populated")


def populate_user_skills_sql(db):
    """Add skills to users using raw SQL"""
    log.info("Adding skills to users using SQL...")
    
    # Get user IDs
    users_result = db.execute(text('SELECT id FROM "USER" LIMIT 10'))
    user_ids = [row[0] for row in users_result]
    
    if not user_ids:
        log.warning("No users found")
        return
    
    # Get skill IDs
    skills_result = db.execute(text('SELECT id FROM "SKILL"'))
    skill_ids = [row[0] for row in skills_result]
    
    if not skill_ids:
        log.warning("No skills found")
        return
    
    # Add skills to users
    proficiency_levels = ["learning", "basic", "intermediate", "advanced", "expert"]
    
    for user_id in user_ids:
        # Add 2-4 random skills per user
        user_skills_count = random.randint(2, 4)
        user_skills = random.sample(skill_ids, min(user_skills_count, len(skill_ids)))
        
        for skill_id in user_skills:
            # Check if user already has this skill
            existing = db.execute(text(
                'SELECT id FROM "USER_SKILL" WHERE user_id = :user_id AND skill_id = :skill_id'
            ), {"user_id": user_id, "skill_id": skill_id}).fetchone()
            
            if not existing:
                user_skill_sql = """
                INSERT INTO "USER_SKILL" (id, user_id, skill_id, proficiency_level, is_primary, created_at)
                VALUES (gen_random_uuid(), :user_id, :skill_id, :proficiency, :is_primary, NOW())
                """
                
                db.execute(text(user_skill_sql), {
                    "user_id": user_id,
                    "skill_id": skill_id,
                    "proficiency": random.choice(proficiency_levels),
                    "is_primary": random.choice([True, False])
                })
                log.info(f"✅ Added skill to user {user_id}")
    
    db.commit()
    log.info("✅ User skills populated")


def populate_project_roles_sql(db):
    """Create project roles using raw SQL"""
    log.info("Creating project roles using SQL...")
    
    # Get project IDs
    projects_result = db.execute(text('SELECT id FROM "PROJECT" LIMIT 5'))
    project_ids = [row[0] for row in projects_result]
    
    if not project_ids:
        log.warning("No projects found")
        return
    
    role_templates = [
        ("Frontend Developer", "Develop user interfaces", "contributor", "part_time", "some"),
        ("Backend Developer", "Develop server-side logic", "contributor", "part_time", "some"),
        ("UI/UX Designer", "Design user interfaces", "contributor", "few_hours", "some"),
        ("DevOps Engineer", "Manage infrastructure", "maintainer", "part_time", "experienced"),
        ("Product Manager", "Manage product strategy", "lead", "part_time", "experienced"),
        ("Data Scientist", "Analyze data and build ML models", "contributor", "part_time", "experienced")
    ]
    
    for project_id in project_ids:
        # Add 2-3 roles per project
        roles_count = random.randint(2, 3)
        selected_roles = random.sample(role_templates, roles_count)
        
        for title, description, responsibility, time_commitment, experience in selected_roles:
            role_sql = """
            INSERT INTO "PROJECT_ROLE" (id, project_id, title, description, responsibility_level, 
                                      time_commitment, slots_available, slots_filled, experience_required, created_at)
            VALUES (gen_random_uuid(), :project_id, :title, :description, :responsibility, 
                   :time_commitment, :slots, 0, :experience, NOW())
            """
            
            db.execute(text(role_sql), {
                "project_id": project_id,
                "title": title,
                "description": description,
                "responsibility": responsibility,
                "time_commitment": time_commitment,
                "slots": random.randint(1, 3),
                "experience": experience
            })
            log.info(f"✅ Added role '{title}' to project {project_id}")
    
    db.commit()
    log.info("✅ Project roles populated")


def populate_contributions_sql(db):
    """Create contributions using raw SQL"""
    log.info("Creating contributions using SQL...")
    
    # Get user and project IDs
    users_result = db.execute(text('SELECT id FROM "USER" LIMIT 10'))
    user_ids = [row[0] for row in users_result]
    
    projects_result = db.execute(text('SELECT id FROM "PROJECT" LIMIT 5'))
    project_ids = [row[0] for row in projects_result]
    
    if not user_ids or not project_ids:
        log.warning("Missing users or projects")
        return
    
    contribution_types = ["code", "design", "documentation", "bug_fix", "feature"]
    statuses = ["submitted", "reviewed", "merged", "rejected"]
    
    for user_id in user_ids:
        # Each user makes 1-3 contributions
        contributions_count = random.randint(1, 3)
        
        for _ in range(contributions_count):
            project_id = random.choice(project_ids)
            contribution_type = random.choice(contribution_types)
            status = random.choice(statuses)
            
            contribution_sql = """
            INSERT INTO "CONTRIBUTION" (id, user_id, project_id, type, title, description, status, 
                                      github_pr_url, submitted_at)
            VALUES (gen_random_uuid(), :user_id, :project_id, :type, :title, :description, :status,
                   :pr_url, :submitted_at)
            """
            
            db.execute(text(contribution_sql), {
                "user_id": user_id,
                "project_id": project_id,
                "type": contribution_type,
                "title": f"{contribution_type.title()} contribution",
                "description": f"User contributed {contribution_type}",
                "status": status,
                "pr_url": f"https://github.com/project/pull/{random.randint(1, 100)}",
                "submitted_at": datetime.utcnow() - timedelta(days=random.randint(1, 30))
            })
            log.info(f"✅ Added {contribution_type} contribution from user {user_id}")
    
    db.commit()
    log.info("✅ Contributions populated")


def populate_applications_sql(db):
    """Create applications using raw SQL"""
    log.info("Creating applications using SQL...")
    
    # Get user and role IDs
    users_result = db.execute(text('SELECT id FROM "USER" LIMIT 10'))
    user_ids = [row[0] for row in users_result]
    
    roles_result = db.execute(text('SELECT id FROM "PROJECT_ROLE"'))
    role_ids = [row[0] for row in roles_result]
    
    if not user_ids or not role_ids:
        log.warning("Missing users or roles")
        return
    
    availabilities = ["immediate", "within_week", "within_month"]
    statuses = ["pending", "accepted", "rejected", "withdrawn"]
    
    for user_id in user_ids:
        # Each user applies to 1-2 roles
        applications_count = random.randint(1, 2)
        user_roles = random.sample(role_ids, min(applications_count, len(role_ids)))
        
        for role_id in user_roles:
            # Check if user already applied
            existing = db.execute(text(
                'SELECT id FROM "APPLICATION" WHERE user_id = :user_id AND project_role_id = :role_id'
            ), {"user_id": user_id, "role_id": role_id}).fetchone()
            
            if not existing:
                application_sql = """
                INSERT INTO "APPLICATION" (id, user_id, project_role_id, portfolio_links, availability, 
                                         status, applied_at)
                VALUES (gen_random_uuid(), :user_id, :role_id, :portfolio, :availability, :status, NOW())
                """
                
                db.execute(text(application_sql), {
                    "user_id": user_id,
                    "role_id": role_id,
                    "portfolio": "https://github.com/user,https://linkedin.com/user",
                    "availability": random.choice(availabilities),
                    "status": random.choice(statuses)
                })
                log.info(f"✅ Added application from user {user_id} for role {role_id}")
    
    db.commit()
    log.info("✅ Applications populated")


def update_contribution_scores_sql(db):
    """Update user contribution scores using raw SQL"""
    log.info("Updating user contribution scores...")
    
    update_sql = """
    UPDATE "USER" 
    SET contribution_score = (
        SELECT COALESCE(COUNT(c.id) * 10, 0) + COALESCE(COUNT(tm.id) * 5, 0)
        FROM "USER" u
        LEFT JOIN "CONTRIBUTION" c ON u.id = c.user_id
        LEFT JOIN "TEAM_MEMBER" tm ON u.id = tm.user_id
        WHERE u.id = "USER".id
        GROUP BY u.id
    )
    """
    
    db.execute(text(update_sql))
    db.commit()
    log.info("✅ User contribution scores updated")


def main():
    """Run the complete test data population"""
    log.info("🚀 Starting complete test data population...")
    
    try:
        with SessionLocal() as db:
            # Step 1: Populate user technologies
            populate_user_technologies_sql(db)
            
            # Step 2: Populate user skills
            populate_user_skills_sql(db)
            
            # Step 3: Create project roles
            populate_project_roles_sql(db)
            
            # Step 4: Create contributions
            populate_contributions_sql(db)
            
            # Step 5: Create applications
            populate_applications_sql(db)
            
            # Step 6: Update contribution scores
            update_contribution_scores_sql(db)
        
        log.info("🎉 Complete test data population completed!")
        log.info("📊 Database now contains comprehensive user interactions for API testing")
        log.info("✅ Users now have technologies, skills, contributions, and applications")
        
    except Exception as e:
        log.error(f"❌ Test data population failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 