#!/usr/bin/env python3
"""
Populate Test Data Script - User Interactions

This script populates the database with test data for user interactions
to properly test the recommendation API endpoints.

Creates:
- User skills (UserSkill)
- Team memberships (TeamMember) 
- Contributions (Contribution)
- Applications (Application)
- Project roles (ProjectRole)
"""

import sys
import os
import random
import uuid
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.postgres.database import SessionLocal
from src.domain.models.schema import (
    User, Project, ProjectRole, TeamMember, Contribution, Application,
    Skill, SkillCategory, UserSkill
)
from src.infrastructure.logger import log


def get_or_create_skill_category(db, name, description):
    """Get existing skill category or create new one"""
    category = db.query(SkillCategory).filter_by(name=name).first()
    if not category:
        category = SkillCategory(
            name=name,
            description=description,
            icon_url=f"https://example.com/icons/{name.lower()}.png"
        )
        db.add(category)
        db.commit()
        db.refresh(category)
    return category


def get_or_create_skill(db, name, category_name, description, is_technical=True):
    """Get existing skill or create new one"""
    skill = db.query(Skill).filter_by(name=name).first()
    if not skill:
        category = get_or_create_skill_category(db, category_name, f"{category_name} skills")
        skill = Skill(
            skill_category_id=category.id,
            name=name,
            description=description,
            is_technical=is_technical
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
    return skill


def populate_user_skills(db):
    """Add skills to existing users"""
    log.info("Adding skills to users...")
    
    # Get existing users and skills
    users = db.query(User).all()
    if not users:
        log.warning("No users found. Please run populate_db.py first.")
        return
    
    # Define skills to add
    skills_data = [
        ("Python", "Backend", "Python programming language", True),
        ("JavaScript", "Frontend", "JavaScript programming language", True),
        ("React", "Frontend", "React.js library", True),
        ("Node.js", "Backend", "Node.js runtime", True),
        ("Docker", "DevOps", "Containerization platform", True),
        ("UI Design", "Design", "User interface design", False),
        ("SEO", "Marketing", "Search Engine Optimization", False),
        ("Technical Writing", "Documentation", "Technical documentation", False)
    ]
    
    # Create skills
    skills = []
    for skill_name, category, description, is_technical in skills_data:
        skill = get_or_create_skill(db, skill_name, category, description, is_technical)
        skills.append(skill)
    
    # Add skills to users
    proficiency_levels = ["learning", "basic", "intermediate", "advanced", "expert"]
    
    for user in users:
        # Add 2-4 random skills per user
        user_skills_count = random.randint(2, 4)
        user_skills = random.sample(skills, user_skills_count)
        
        for skill in user_skills:
            # Check if user already has this skill
            existing = db.query(UserSkill).filter_by(user_id=user.id, skill_id=skill.id).first()
            if not existing:
                user_skill = UserSkill(
                    user_id=user.id,
                    skill_id=skill.id,
                    proficiency_level=random.choice(proficiency_levels),
                    is_primary=random.choice([True, False])
                )
                db.add(user_skill)
                log.info(f"✅ Added skill '{skill.name}' to user '{user.username}'")
    
    db.commit()
    log.info("✅ User skills populated")


def populate_project_roles(db):
    """Create project roles for existing projects"""
    log.info("Creating project roles...")
    
    projects = db.query(Project).all()
    if not projects:
        log.warning("No projects found. Please run populate_db.py first.")
        return
    
    role_templates = [
        {
            "title": "Frontend Developer",
            "description": "Develop user interfaces and frontend features",
            "responsibility_level": "contributor",
            "time_commitment": "part_time",
            "experience_required": "some"
        },
        {
            "title": "Backend Developer", 
            "description": "Develop server-side logic and APIs",
            "responsibility_level": "contributor",
            "time_commitment": "part_time",
            "experience_required": "some"
        },
        {
            "title": "UI/UX Designer",
            "description": "Design user interfaces and user experience",
            "responsibility_level": "contributor", 
            "time_commitment": "few_hours",
            "experience_required": "some"
        },
        {
            "title": "DevOps Engineer",
            "description": "Manage infrastructure and deployment",
            "responsibility_level": "maintainer",
            "time_commitment": "part_time",
            "experience_required": "experienced"
        },
        {
            "title": "Technical Writer",
            "description": "Write documentation and guides",
            "responsibility_level": "contributor",
            "time_commitment": "few_hours", 
            "experience_required": "none"
        }
    ]
    
    for project in projects:
        # Add 2-3 roles per project
        roles_count = random.randint(2, 3)
        selected_roles = random.sample(role_templates, roles_count)
        
        for role_template in selected_roles:
            role = ProjectRole(
                project_id=project.id,
                slots_available=random.randint(1, 3),
                **role_template
            )
            db.add(role)
            log.info(f"✅ Added role '{role.title}' to project '{project.title}'")
    
    db.commit()
    log.info("✅ Project roles populated")


def populate_team_memberships(db):
    """Add users to project teams"""
    log.info("Creating team memberships...")
    
    users = db.query(User).all()
    projects = db.query(Project).all()
    roles = db.query(ProjectRole).all()
    
    if not users or not projects or not roles:
        log.warning("Missing data. Please run populate_db.py first.")
        return
    
    # Add some users to project teams
    for project in projects:
        # Add 1-3 team members per project
        team_size = random.randint(1, 3)
        project_users = random.sample(users, min(team_size, len(users)))
        
        for user in project_users:
            # Get a random role for this project
            project_roles = [r for r in roles if r.project_id == project.id]
            if project_roles:
                role = random.choice(project_roles)
                
                # Check if user is already a team member
                existing = db.query(TeamMember).filter_by(
                    user_id=user.id, 
                    project_id=project.id
                ).first()
                
                if not existing:
                    team_member = TeamMember(
                        user_id=user.id,
                        project_id=project.id,
                        project_role_id=role.id,
                        status="active",
                        contributions_count=random.randint(0, 5)
                    )
                    db.add(team_member)
                    log.info(f"✅ Added user '{user.username}' to project '{project.title}' as '{role.title}'")
    
    db.commit()
    log.info("✅ Team memberships populated")


def populate_contributions(db):
    """Create contributions for users"""
    log.info("Creating contributions...")
    
    users = db.query(User).all()
    projects = db.query(Project).all()
    
    if not users or not projects:
        log.warning("Missing data. Please run populate_db.py first.")
        return
    
    contribution_types = ["code", "design", "documentation", "bug_fix", "feature"]
    statuses = ["submitted", "reviewed", "merged", "rejected"]
    
    # Create contributions for each user
    for user in users:
        # Each user makes 1-3 contributions
        contributions_count = random.randint(1, 3)
        
        for _ in range(contributions_count):
            project = random.choice(projects)
            contribution_type = random.choice(contribution_types)
            status = random.choice(statuses)
            
            contribution = Contribution(
                user_id=user.id,
                project_id=project.id,
                type=contribution_type,
                title=f"{contribution_type.title()} contribution to {project.title}",
                description=f"User {user.username} contributed {contribution_type} to {project.title}",
                status=status,
                github_pr_url=f"https://github.com/{project.title}/pull/{random.randint(1, 100)}",
                submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            
            # Add merge date if merged
            if status == "merged":
                contribution.merged_at = contribution.submitted_at + timedelta(days=random.randint(1, 7))
            
            db.add(contribution)
            log.info(f"✅ Added {contribution_type} contribution from '{user.username}' to '{project.title}'")
    
    db.commit()
    log.info("✅ Contributions populated")


def populate_applications(db):
    """Create applications for project roles"""
    log.info("Creating applications...")
    
    users = db.query(User).all()
    roles = db.query(ProjectRole).all()
    
    if not users or not roles:
        log.warning("Missing data. Please run populate_db.py first.")
        return
    
    availabilities = ["immediate", "within_week", "within_month"]
    statuses = ["pending", "accepted", "rejected", "withdrawn"]
    
    # Create applications
    for user in users:
        # Each user applies to 1-2 roles
        applications_count = random.randint(1, 2)
        user_roles = random.sample(roles, min(applications_count, len(roles)))
        
        for role in user_roles:
            # Check if user already applied
            existing = db.query(Application).filter_by(
                user_id=user.id,
                project_role_id=role.id
            ).first()
            
            if not existing:
                application = Application(
                    user_id=user.id,
                    project_role_id=role.id,
                    portfolio_links="https://github.com/user,https://linkedin.com/user",
                    availability=random.choice(availabilities),
                    status=random.choice(statuses),
                    applied_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                )
                
                db.add(application)
                log.info(f"✅ Added application from '{user.username}' for role '{role.title}'")
    
    db.commit()
    log.info("✅ Applications populated")


def update_user_contribution_scores(db):
    """Update user contribution scores based on their contributions"""
    log.info("Updating user contribution scores...")
    
    users = db.query(User).all()
    
    for user in users:
        # Count contributions
        contributions_count = db.query(Contribution).filter_by(user_id=user.id).count()
        
        # Count team memberships
        team_memberships_count = db.query(TeamMember).filter_by(user_id=user.id).count()
        
        # Calculate score (simple formula)
        score = (contributions_count * 10) + (team_memberships_count * 5)
        
        # Update user
        user.contribution_score = score
        log.info(f"✅ Updated '{user.username}' contribution score to {score}")
    
    db.commit()
    log.info("✅ User contribution scores updated")


def main():
    """Run the complete test data population"""
    log.info("🚀 Starting test data population for user interactions...")
    
    try:
        with SessionLocal() as db:
            # Step 1: Populate user skills
            populate_user_skills(db)
            
            # Step 2: Create project roles
            populate_project_roles(db)
            
            # Step 3: Add team memberships
            populate_team_memberships(db)
            
            # Step 4: Create contributions
            populate_contributions(db)
            
            # Step 5: Create applications
            populate_applications(db)
            
            # Step 6: Update contribution scores
            update_user_contribution_scores(db)
        
        log.info("🎉 Test data population completed successfully!")
        log.info("📊 Database now contains user interactions for API testing")
        
    except Exception as e:
        log.error(f"❌ Test data population failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 