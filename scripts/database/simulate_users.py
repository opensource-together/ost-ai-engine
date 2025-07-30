#!/usr/bin/env python3
"""
User Simulation Script

This script creates realistic user profiles and simulates coherent interactions
with existing projects in the database.
Uses classes for better organization and maintainability.
"""

import argparse
import random
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from src.domain.models.schema import (
    ProjectRoleApplication,
    Project,
    ProjectRole,
    TeamMember,
    User,
    UserTechStack,
    TechStack,
    Category,
)
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import SessionLocal


class UserSimulator:
    """Handles creation of realistic user profiles and interactions."""
    
    def __init__(self, db: Session):
        self.db = db
        self._faker = Faker()
        
        # Define user categories with realistic profiles
        self.user_categories = {
            "Frontend Developer": {
                "tech_stacks": ["React", "Vue.js", "TypeScript", "CSS", "HTML", "Figma"],
                "interaction_weights": {"application": 0.6, "member": 0.4},
                "preferred_categories": ["Education", "E-commerce", "Social", "Productivity"]
            },
            "Backend Developer": {
                "tech_stacks": ["Python", "Node.js", "Java", "Go", "PostgreSQL", "Docker"],
                "interaction_weights": {"application": 0.5, "member": 0.5},
                "preferred_categories": ["Finance", "DevTools", "E-commerce", "Social"]
            },
            "Mobile Developer": {
                "tech_stacks": ["React Native", "Flutter", "Swift", "Kotlin", "Git", "GitHub"],
                "interaction_weights": {"application": 0.7, "member": 0.3},
                "preferred_categories": ["Gaming", "Social", "E-commerce", "Education"]
            },
            "Data Scientist": {
                "tech_stacks": ["Python", "Pandas", "PostgreSQL", "GitHub"],
                "interaction_weights": {"application": 0.4, "member": 0.6},
                "preferred_categories": ["Finance", "Healthcare", "Education", "DevTools"]
            },
            "DevOps Engineer": {
                "tech_stacks": ["Docker", "Kubernetes", "AWS", "Git", "Linux"],
                "interaction_weights": {"application": 0.5, "member": 0.5},
                "preferred_categories": ["DevTools", "Finance", "E-commerce"]
            }
        }
    
    def simulate_users(self, num_users: int = 100, interactions_per_user: int = 20):
        """Create users and simulate their interactions with projects."""
        
        log.info(f"🚀 Starting user simulation for {num_users} users...")
        
        # Get existing projects and tech stacks
        projects = self.db.query(Project).all()
        tech_stacks = self.db.query(TechStack).all()
        categories = self.db.query(Category).all()
        
        if not projects:
            log.error("❌ No projects found in database. Run scraping.py first.")
            return
        
        if not tech_stacks:
            log.error("❌ No tech stacks found. Run simulate_projects.py first.")
            return
        
        # Create users
        users = self._create_users(num_users)
        
        # Create user profiles (tech stacks)
        self._create_user_profiles(users, tech_stacks)
        
        # Simulate interactions
        self._simulate_interactions(users, projects, interactions_per_user)
        
        log.info("🎉 User simulation completed successfully!")
        self._log_statistics()
    
    def _create_users(self, num_users: int):
        """Create realistic user profiles."""
        log.info(f"Creating {num_users} users...")
        
        users = []
        categories = list(self.user_categories.keys())
        
        for i in range(num_users):
            category = random.choice(categories)
            category_data = self.user_categories[category]
            
            # Create realistic user data
            first_name = self._faker.first_name()
            last_name = self._faker.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}_{i}"
            
            user = User(
                username=username,
                email=f"{username}@example.com",
                login=username,  # GitHub login
                avatar_url=f"https://github.com/{username}.png",
                bio=f"{category} with {random.randint(1, 8)} years of experience in software development.",
                location=self._faker.city(),
                company=random.choice([None, "Tech Corp", "Startup Inc", "Big Company", "Freelance"]),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            users.append(user)
        
        self.db.add_all(users)
        self.db.commit()
        
        log.info(f"✅ Created {len(users)} users")
        return users
    
    def _create_user_profiles(self, users: list, tech_stacks: list):
        """Create user tech stacks based on their category."""
        log.info("Creating user profiles (tech stacks)...")
        
        user_tech_stacks = []
        
        for user in users:
            # Determine user category based on username or random choice
            category = self._determine_user_category(user)
            category_data = self.user_categories[category]
            
            # Add primary tech stacks
            for tech_name in category_data["tech_stacks"]:
                tech = next((t for t in tech_stacks if t.name == tech_name), None)
                if tech:
                    user_tech_stacks.append(UserTechStack(
                        user_id=user.id,
                        tech_stack_id=tech.id
                    ))
            
            # Add some secondary tech stacks
            num_secondary_techs = random.randint(1, 3)
            available_techs = [t for t in tech_stacks if t.name not in category_data["tech_stacks"]]
            
            if available_techs:
                secondary_techs = random.sample(available_techs, min(num_secondary_techs, len(available_techs)))
                for tech in secondary_techs:
                    user_tech_stacks.append(UserTechStack(
                        user_id=user.id,
                        tech_stack_id=tech.id
                    ))
        
        self.db.add_all(user_tech_stacks)
        self.db.commit()
        
        log.info(f"✅ Created {len(user_tech_stacks)} user tech stacks")
    
    def _determine_user_category(self, user: User) -> str:
        """Determine user category based on username or random choice."""
        username = user.username.lower()
        
        if any(keyword in username for keyword in ["frontend", "ui", "ux", "react", "vue"]):
            return "Frontend Developer"
        elif any(keyword in username for keyword in ["backend", "api", "python", "java", "go"]):
            return "Backend Developer"
        elif any(keyword in username for keyword in ["mobile", "ios", "android", "flutter"]):
            return "Mobile Developer"
        elif any(keyword in username for keyword in ["data", "ml", "ai", "scientist"]):
            return "Data Scientist"
        elif any(keyword in username for keyword in ["devops", "ops", "infra", "cloud"]):
            return "DevOps Engineer"
        else:
            return random.choice(list(self.user_categories.keys()))
    
    def _simulate_interactions(self, users: list, projects: list, interactions_per_user: int):
        """Simulate realistic user interactions with projects."""
        log.info(f"Simulating {interactions_per_user} interactions per user...")
        
        all_interactions = []
        team_member_cache = set()
        application_cache = set()
        
        for user in users:
            category = self._determine_user_category(user)
            category_data = self.user_categories[category]
            
            # Find projects that match user's profile
            matching_projects = self._find_matching_projects(user, projects, category_data)
            
            # Generate interactions for this user
            user_interactions = []
            
            for _ in range(interactions_per_user):
                project = random.choice(matching_projects)
                
                # Choose interaction type based on weights
                interaction_type = random.choices(
                    list(category_data["interaction_weights"].keys()),
                    weights=list(category_data["interaction_weights"].values())
                )[0]
                
                if interaction_type == "application":
                    # Get project roles for this project
                    project_roles = self.db.query(ProjectRole).filter_by(project_id=project.id).all()
                    if project_roles:
                        role = random.choice(project_roles)
                        
                        if (user.id, role.id) not in application_cache:
                            user_interactions.append(ProjectRoleApplication(
                                project_id=project.id,
                                project_title=project.title,
                                project_role_id=role.id,
                                project_role_title=role.title,
                                project_description=project.description,
                                user_id=user.id,  # ADDED missing field
                                status=random.choice(["pending", "accepted", "rejected"]),
                                motivation_letter=f"I'm interested in contributing to {project.title} as a {role.title}.",
                                applied_at=self._faker.date_time_between(
                                    start_date="-6m", end_date="now"
                                )
                            ))
                            application_cache.add((user.id, role.id))
                
                elif interaction_type == "member":
                    if (user.id, project.id) not in team_member_cache:
                        joined_date = self._faker.date_time_between(
                            start_date="-1y", end_date="-1m"
                        )
                        
                        user_interactions.append(TeamMember(
                            user_id=user.id,
                            project_id=project.id,
                            joined_at=joined_date
                        ))
                        team_member_cache.add((user.id, project.id))
            
            all_interactions.extend(user_interactions)
        
        self.db.add_all(all_interactions)
        self.db.commit()
        
        log.info(f"✅ Created {len(all_interactions)} user interactions")
    
    def _find_matching_projects(self, user: User, projects: list, category_data: dict) -> list:
        """Find projects that match user's profile."""
        matching_projects = []
        
        # Get user's tech stacks with a join
        from sqlalchemy.orm import joinedload
        user_tech_stacks = self.db.query(UserTechStack, TechStack).join(
            TechStack, UserTechStack.tech_stack_id == TechStack.id
        ).filter(UserTechStack.user_id == user.id).all()
        
        tech_names = [tech_stack.name for _, tech_stack in user_tech_stacks]
        
        for project in projects:
            # Simple matching based on project description and tech stacks
            if any(tech.lower() in project.description.lower() for tech in tech_names if tech):
                matching_projects.append(project)
            elif random.random() < 0.3:  # 30% chance for random projects
                matching_projects.append(project)
        
        # If no matches, return some random projects
        if not matching_projects:
            return random.sample(projects, min(10, len(projects)))
        
        return matching_projects
    
    def _log_statistics(self):
        """Log final statistics."""
        log.info("📊 User Simulation Statistics:")
        log.info(f"   Total Users: {self.db.query(User).count()}")
        log.info(f"   Total User Tech Stacks: {self.db.query(UserTechStack).count()}")
        log.info(f"   Total Project Role Applications: {self.db.query(ProjectRoleApplication).count()}")
        log.info(f"   Total Team Memberships: {self.db.query(TeamMember).count()}")
        
        # Show some user examples
        users = self.db.query(User).limit(5).all()
        log.info("👥 Sample Users:")
        for user in users:
            applications = self.db.query(ProjectRoleApplication).filter_by(user_id=user.id).count()
            memberships = self.db.query(TeamMember).filter_by(user_id=user.id).count()
            tech_stacks = self.db.query(UserTechStack).filter_by(user_id=user.id).count()
            log.info(f"   {user.username}: {applications} applications, {memberships} memberships, {tech_stacks} tech stacks")


def main():
    """Main function to run the user simulation."""
    parser = argparse.ArgumentParser(
        description="Simulate realistic user profiles and interactions."
    )
    parser.add_argument(
        "--num-users",
        type=int,
        default=100,
        help="Number of users to create (default: 100).",
    )
    parser.add_argument(
        "--interactions-per-user",
        type=int,
        default=20,
        help="Number of interactions per user (default: 20).",
    )
    
    args = parser.parse_args()

    log.info("🚀 Starting user simulation...")
    
    db_session = SessionLocal()
    try:
        simulator = UserSimulator(db_session)
        simulator.simulate_users(
            num_users=args.num_users,
            interactions_per_user=args.interactions_per_user
        )
    finally:
        db_session.close()
        log.info("Script finished. Database session closed.")


if __name__ == "__main__":
    main() 