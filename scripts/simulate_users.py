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
    Application,
    Contribution,
    Project,
    ProjectRole,
    TeamMember,
    User,
    UserSkill,
    UserTechnology,
    CommunityMember,
    Skill,
    Technology,
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
                "skills": ["React", "Vue.js", "TypeScript", "CSS", "HTML", "UI Design"],
                "technologies": ["React", "Vue.js", "TypeScript", "CSS", "HTML", "Figma"],
                "interaction_weights": {"contribution": 0.4, "application": 0.4, "member": 0.2},
                "contribution_types": ["design", "code", "documentation"],
                "preferred_domains": ["Education", "E-commerce", "Social", "Productivity"]
            },
            "Backend Developer": {
                "skills": ["Python", "Node.js", "Java", "Go", "Database Design", "API Design"],
                "technologies": ["Python", "Node.js", "Java", "Go", "PostgreSQL", "Docker"],
                "interaction_weights": {"contribution": 0.5, "application": 0.3, "member": 0.2},
                "contribution_types": ["code", "bug_fix", "feature", "documentation"],
                "preferred_domains": ["Finance", "DevTools", "E-commerce", "Social"]
            },
            "Mobile Developer": {
                "skills": ["React Native", "Flutter", "iOS Development", "Android Development"],
                "technologies": ["React Native", "Flutter", "Git", "GitHub"],
                "interaction_weights": {"contribution": 0.3, "application": 0.5, "member": 0.2},
                "contribution_types": ["code", "bug_fix", "feature"],
                "preferred_domains": ["Gaming", "Social", "E-commerce", "Education"]
            },
            "Data Scientist": {
                "skills": ["Python", "Machine Learning", "Data Analysis", "SQL", "Pandas"],
                "technologies": ["Python", "Pandas", "PostgreSQL", "GitHub"],
                "interaction_weights": {"contribution": 0.6, "application": 0.2, "member": 0.2},
                "contribution_types": ["code", "bug_fix", "feature"],
                "preferred_domains": ["Finance", "Santé", "Education", "DevTools"]
            },
            "DevOps Engineer": {
                "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Security"],
                "technologies": ["Docker", "Kubernetes", "AWS", "Git", "Linux"],
                "interaction_weights": {"contribution": 0.4, "application": 0.3, "member": 0.3},
                "contribution_types": ["code", "bug_fix", "feature", "documentation"],
                "preferred_domains": ["DevTools", "Finance", "E-commerce"]
            }
        }
    
    def simulate_users(self, num_users: int = 100, interactions_per_user: int = 20):
        """Create users and simulate their interactions with projects."""
        
        log.info(f"🚀 Starting user simulation for {num_users} users...")
        
        # Get existing projects and skills/technologies
        projects = self.db.query(Project).all()
        skills = self.db.query(Skill).all()
        technologies = self.db.query(Technology).all()
        
        if not projects:
            log.error("❌ No projects found in database. Run scraping.py first.")
            return
        
        if not skills or not technologies:
            log.error("❌ No skills or technologies found. Run create_tables.py first.")
            return
        
        # Create users
        users = self._create_users(num_users)
        
        # Create user profiles (skills and technologies)
        self._create_user_profiles(users, skills, technologies)
        
        # Simulate interactions
        self._simulate_interactions(users, projects, interactions_per_user)
        
        # Update contribution scores
        self._update_contribution_scores(users)
        
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
                bio=f"{category} with {random.randint(1, 8)} years of experience in software development.",
                github_username=f"{username}",
                linkedin_url=f"https://linkedin.com/in/{username}",
                github_url=f"https://github.com/{username}",
                portfolio_url=f"https://{username}.dev",
                contribution_score=0,  # Will be updated later
                level=random.choice(["beginner", "intermediate", "advanced"]),
                is_open_to_hire=random.choice([True, False]),
                location=self._faker.city(),
                timezone=random.choice(["Europe/Paris", "America/New_York", "Asia/Tokyo", "Europe/London"])
            )
            users.append(user)
        
        self.db.add_all(users)
        self.db.commit()
        
        log.info(f"✅ Created {len(users)} users")
        return users
    
    def _create_user_profiles(self, users: list, skills: list, technologies: list):
        """Create user skills and technologies based on their category."""
        log.info("Creating user profiles (skills and technologies)...")
        
        user_skills = []
        user_technologies = []
        
        for user in users:
            # Determine user category based on username or random choice
            category = self._determine_user_category(user)
            category_data = self.user_categories[category]
            
            # Add primary skills and technologies
            for skill_name in category_data["skills"]:
                skill = next((s for s in skills if s.name == skill_name), None)
                if skill:
                    user_skills.append(UserSkill(
                        user_id=user.id,
                        skill_id=skill.id,
                        proficiency_level=random.choice(["basic", "intermediate", "advanced"]),
                        is_primary=True
                    ))
            
            for tech_name in category_data["technologies"]:
                tech = next((t for t in technologies if t.name == tech_name), None)
                if tech:
                    user_technologies.append(UserTechnology(
                        user_id=user.id,
                        technology_id=tech.id,
                        proficiency_level=random.choice(["basic", "intermediate", "advanced"]),
                        is_primary=True
                    ))
            
            # Add some secondary skills and technologies
            num_secondary_skills = random.randint(1, 3)
            num_secondary_techs = random.randint(1, 3)
            
            available_skills = [s for s in skills if s.name not in category_data["skills"]]
            available_techs = [t for t in technologies if t.name not in category_data["technologies"]]
            
            if available_skills:
                secondary_skills = random.sample(available_skills, min(num_secondary_skills, len(available_skills)))
                for skill in secondary_skills:
                    user_skills.append(UserSkill(
                        user_id=user.id,
                        skill_id=skill.id,
                        proficiency_level=random.choice(["basic", "intermediate"]),
                        is_primary=False
                    ))
            
            if available_techs:
                secondary_techs = random.sample(available_techs, min(num_secondary_techs, len(available_techs)))
                for tech in secondary_techs:
                    user_technologies.append(UserTechnology(
                        user_id=user.id,
                        technology_id=tech.id,
                        proficiency_level=random.choice(["basic", "intermediate"]),
                        is_primary=False
                    ))
        
        self.db.add_all(user_skills)
        self.db.add_all(user_technologies)
        self.db.commit()
        
        log.info(f"✅ Created {len(user_skills)} user skills and {len(user_technologies)} user technologies")
    
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
                
                if interaction_type == "contribution":
                    contribution_type = random.choice(category_data["contribution_types"])
                    
                    user_interactions.append(Contribution(
                        user_id=user.id,
                        project_id=project.id,
                        type=contribution_type,
                        title=f"Contribution to {project.title}",
                        description=f"User contribution to {project.title}",
                        status=random.choice(["submitted", "reviewed", "merged"]),
                        submitted_at=self._faker.date_time_between(
                            start_date="-1y", end_date="now"
                        )
                    ))
                
                elif interaction_type == "application":
                    # Get project roles for this project
                    project_roles = self.db.query(ProjectRole).filter_by(project_id=project.id).all()
                    if project_roles:
                        role = random.choice(project_roles)
                        
                        if (user.id, role.id) not in application_cache:
                            user_interactions.append(Application(
                                user_id=user.id,
                                project_role_id=role.id,
                                portfolio_links=f'["https://github.com/{user.username}", "https://linkedin.com/in/{user.username}"]',
                                availability=random.choice(["immediate", "within_week", "within_month"]),
                                status=random.choice(["pending", "accepted", "rejected"]),
                                applied_at=self._faker.date_time_between(
                                    start_date="-6m", end_date="now"
                                )
                            ))
                            application_cache.add((user.id, role.id))
                
                elif interaction_type == "member":
                    project_roles = self.db.query(ProjectRole).filter_by(project_id=project.id).all()
                    if project_roles:
                        role = random.choice(project_roles)
                        
                        if (user.id, project.id) not in team_member_cache:
                            joined_date = self._faker.date_time_between(
                                start_date="-1y", end_date="-1m"
                            )
                            
                            user_interactions.append(TeamMember(
                                user_id=user.id,
                                project_id=project.id,
                                project_role_id=role.id,
                                status="active",
                                contributions_count=random.randint(1, 15),
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
        
        # Get user's skills and technologies
        user_skills = self.db.query(UserSkill).filter_by(user_id=user.id).all()
        user_technologies = self.db.query(UserTechnology).filter_by(user_id=user.id).all()
        
        skill_names = [us.skill.name for us in user_skills if us.skill]
        tech_names = [ut.technology.name for ut in user_technologies if ut.technology]
        
        for project in projects:
            # Simple matching based on language and project type
            if any(skill.lower() in project.language.lower() for skill in skill_names if skill):
                matching_projects.append(project)
            elif any(tech.lower() in project.language.lower() for tech in tech_names if tech):
                matching_projects.append(project)
            elif random.random() < 0.3:  # 30% chance for random projects
                matching_projects.append(project)
        
        # If no matches, return some random projects
        if not matching_projects:
            return random.sample(projects, min(10, len(projects)))
        
        return matching_projects
    
    def _update_contribution_scores(self, users: list):
        """Update user contribution scores based on their interactions."""
        log.info("Updating user contribution scores...")
        
        for user in users:
            # Count contributions
            contributions_count = self.db.query(Contribution).filter_by(user_id=user.id).count()
            
            # Count team memberships
            team_memberships_count = self.db.query(TeamMember).filter_by(user_id=user.id).count()
            
            # Count applications
            applications_count = self.db.query(Application).filter_by(user_id=user.id).count()
            
            # Calculate score
            score = contributions_count * 10 + team_memberships_count * 5 + applications_count * 2
            
            user.contribution_score = score
        
        self.db.commit()
        log.info("✅ Updated user contribution scores")
    
    def _log_statistics(self):
        """Log final statistics."""
        log.info("📊 User Simulation Statistics:")
        log.info(f"   Total Users: {self.db.query(User).count()}")
        log.info(f"   Total User Skills: {self.db.query(UserSkill).count()}")
        log.info(f"   Total User Technologies: {self.db.query(UserTechnology).count()}")
        log.info(f"   Total Contributions: {self.db.query(Contribution).count()}")
        log.info(f"   Total Applications: {self.db.query(Application).count()}")
        log.info(f"   Total Team Memberships: {self.db.query(TeamMember).count()}")
        log.info(f"   Total Community Members: {self.db.query(CommunityMember).count()}")
        
        # Show some user examples
        users = self.db.query(User).limit(5).all()
        log.info("👥 Sample Users:")
        for user in users:
            contributions = self.db.query(Contribution).filter_by(user_id=user.id).count()
            applications = self.db.query(Application).filter_by(user_id=user.id).count()
            memberships = self.db.query(TeamMember).filter_by(user_id=user.id).count()
            log.info(f"   {user.username}: {contributions} contributions, {applications} applications, {memberships} memberships")


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