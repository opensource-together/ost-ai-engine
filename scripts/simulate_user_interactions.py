#!/usr/bin/env python3
"""
Script to simulate user interactions (TeamMember, Contribution, Application)
based on existing UserSkill and UserTechnology data.
"""

import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.infrastructure.postgres.database import SessionLocal
from src.domain.models.schema import (
    User, Project, ProjectRole, TeamMember, Contribution, Application,
    UserSkill, UserTechnology, Skill, Technology
)


def simulate_team_memberships(db: Session, num_interactions: int = 20):
    """Simulate team memberships for users."""
    print("🔄 Simulating team memberships...")
    
    # Get existing users and projects
    users = db.query(User).all()
    projects = db.query(Project).all()
    project_roles = db.query(ProjectRole).all()
    
    if not users or not projects or not project_roles:
        print("⚠️ Missing users, projects, or project roles")
        return
    
    # Create team memberships
    for _ in range(min(num_interactions, len(users) * 2)):
        user = random.choice(users)
        project_role = random.choice(project_roles)
        
        # Check if membership already exists
        existing = db.query(TeamMember).filter(
            TeamMember.user_id == user.id,
            TeamMember.project_id == project_role.project_id
        ).first()
        
        if not existing:
            team_member = TeamMember(
                id=uuid.uuid4(),
                user_id=user.id,
                project_id=project_role.project_id,
                project_role_id=project_role.id,
                status=random.choice(["active", "inactive"]),
                contributions_count=random.randint(0, 10),
                joined_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            db.add(team_member)
    
    db.commit()
    print(f"✅ Created team memberships")


def simulate_contributions(db: Session, num_interactions: int = 30):
    """Simulate contributions for users."""
    print("🔄 Simulating contributions...")
    
    # Get existing users and projects
    users = db.query(User).all()
    projects = db.query(Project).all()
    
    if not users or not projects:
        print("⚠️ Missing users or projects")
        return
    
    contribution_types = ["code", "design", "documentation", "bug_fix", "feature", "other"]
    statuses = ["submitted", "reviewed", "merged", "rejected"]
    
    # Create contributions
    for _ in range(min(num_interactions, len(users) * 3)):
        user = random.choice(users)
        project = random.choice(projects)
        
        contribution = Contribution(
            id=uuid.uuid4(),
            user_id=user.id,
            project_id=project.id,
            type=random.choice(contribution_types),
            title=f"Contribution to {project.title}",
            description=f"User contribution to project {project.title}",
            status=random.choice(statuses),
            submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 180))
        )
        
        if contribution.status in ["reviewed", "merged"]:
            contribution.reviewed_by = random.choice(users).id
            contribution.merged_at = contribution.submitted_at + timedelta(days=random.randint(1, 30))
        
        db.add(contribution)
    
    db.commit()
    print(f"✅ Created contributions")


def simulate_applications(db: Session, num_interactions: int = 25):
    """Simulate applications for project roles."""
    print("🔄 Simulating applications...")
    
    # Get existing users and project roles
    users = db.query(User).all()
    project_roles = db.query(ProjectRole).all()
    
    if not users or not project_roles:
        print("⚠️ Missing users or project roles")
        return
    
    availabilities = ["immediate", "within_week", "within_month"]
    statuses = ["pending", "accepted", "rejected", "withdrawn"]
    
    # Create applications
    for _ in range(min(num_interactions, len(users) * 2)):
        user = random.choice(users)
        project_role = random.choice(project_roles)
        
        # Check if application already exists
        existing = db.query(Application).filter(
            Application.user_id == user.id,
            Application.project_role_id == project_role.id
        ).first()
        
        if not existing:
            application = Application(
                id=uuid.uuid4(),
                user_id=user.id,
                project_role_id=project_role.id,
                portfolio_links='["https://github.com/user", "https://linkedin.com/user"]',
                availability=random.choice(availabilities),
                status=random.choice(statuses),
                applied_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
            )
            
            if application.status in ["accepted", "rejected"]:
                application.reviewed_by = random.choice(users).id
                application.reviewed_at = application.applied_at + timedelta(days=random.randint(1, 14))
                application.review_message = f"Application {application.status}"
            
            db.add(application)
    
    db.commit()
    print(f"✅ Created applications")


def create_project_roles_if_missing(db: Session):
    """Create project roles if they don't exist."""
    print("🔄 Checking for project roles...")
    
    projects = db.query(Project).all()
    if not projects:
        print("⚠️ No projects found")
        return
    
    role_titles = ["Developer", "Designer", "Documentation Writer", "QA Tester", "Project Manager"]
    responsibility_levels = ["contributor", "maintainer", "lead"]
    time_commitments = ["few_hours", "part_time", "full_time"]
    experience_levels = ["none", "some", "experienced"]
    
    for project in projects:
        # Check if project already has roles
        existing_roles = db.query(ProjectRole).filter(ProjectRole.project_id == project.id).count()
        
        if existing_roles == 0:
            # Create 2-3 roles per project
            for i in range(random.randint(2, 3)):
                role = ProjectRole(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    title=random.choice(role_titles),
                    description=f"Role for {project.title}",
                    responsibility_level=random.choice(responsibility_levels),
                    time_commitment=random.choice(time_commitments),
                    slots_available=random.randint(1, 3),
                    slots_filled=0,
                    experience_required=random.choice(experience_levels)
                )
                db.add(role)
    
    db.commit()
    print(f"✅ Created project roles")


def main():
    """Main function to simulate all user interactions."""
    print("🚀 Starting user interaction simulation...")
    
    db = SessionLocal()
    
    try:
        # Create project roles if missing
        create_project_roles_if_missing(db)
        
        # Simulate interactions
        simulate_team_memberships(db, num_interactions=20)
        simulate_contributions(db, num_interactions=30)
        simulate_applications(db, num_interactions=25)
        
        # Verify data
        team_members = db.query(TeamMember).count()
        contributions = db.query(Contribution).count()
        applications = db.query(Application).count()
        
        print(f"\n📊 Simulation Results:")
        print(f"- Team Memberships: {team_members}")
        print(f"- Contributions: {contributions}")
        print(f"- Applications: {applications}")
        
        print("\n✅ User interaction simulation completed!")
        
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main() 