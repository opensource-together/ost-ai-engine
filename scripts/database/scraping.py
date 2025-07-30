#!/usr/bin/env python3
"""
Project Scraping and Database Population Script

This script scrapes GitHub repositories and populates the database with project data.
Uses classes for better organization and maintainability.
"""

import argparse
import os
import random
from datetime import datetime

from faker import Faker
from sqlalchemy.orm import Session

from src.domain.models.schema import (
    Project,
    ProjectRole,
    ProjectTechStack,
    ProjectCategory,
    ProjectRoleTechStack,
    KeyFeature,
    ProjectGoal,
    TechStack,
    Category,
    User,
)
from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import SessionLocal, engine
from src.infrastructure.scraping.github_scraper import GithubScraper


class MockGithubScraper:
    """A mock scraper that generates fake GitHub project data using Faker."""

    def __init__(self):
        self._faker = Faker()

    def get_repositories_by_names(self, names):
        """Generates a list of fake repositories from a list of names."""
        total_repos = len(names)
        print(f"Generating {total_repos} fake repositories by name...")
        
        repos = []
        for i, name in enumerate(names, 1):
            print(f"Generating fake repository {i}/{total_repos}: {name}")
            repos.append(self._generate_fake_project(name))
        
        print(f"Successfully generated {len(repos)}/{total_repos} fake repositories.")
        return repos

    def get_repositories(self, query, limit):
        """Generates a list of fake repositories up to a given limit."""
        print(f"Generating {limit} fake repositories for query: '{query}'...")
        
        repos = []
        for i in range(limit):
            print(f"Generating fake repository {i+1}/{limit}: repo-{i}")
            repos.append(self._generate_fake_project(f"repo-{i}"))
        
        print(f"Successfully generated {len(repos)} fake repositories.")
        return repos

    def _generate_fake_project(self, name):
        """Generates a single fake project dictionary with coherent data."""
        # Define project categories with coherent languages and topics
        project_categories = [
            {
                "language": "Python",
                "topics": ["python", "data-science", "machine-learning", "api"],
                "project_type": "library",
                "difficulty": "medium"
            },
            {
                "language": "JavaScript", 
                "topics": ["javascript", "react", "frontend", "web"],
                "project_type": "application",
                "difficulty": "easy"
            },
            {
                "language": "TypeScript",
                "topics": ["typescript", "react", "frontend", "web"],
                "project_type": "application", 
                "difficulty": "medium"
            },
            {
                "language": "Go",
                "topics": ["go", "backend", "api", "microservices"],
                "project_type": "tool",
                "difficulty": "hard"
            },
            {
                "language": "Rust",
                "topics": ["rust", "systems", "performance", "backend"],
                "project_type": "library",
                "difficulty": "hard"
            },
            {
                "language": "Java",
                "topics": ["java", "spring-boot", "backend", "api"],
                "project_type": "application",
                "difficulty": "medium"
            },
            {
                "language": "C#",
                "topics": ["csharp", "dotnet", "backend", "api"],
                "project_type": "application",
                "difficulty": "medium"
            },
            {
                "language": "PHP",
                "topics": ["php", "laravel", "web", "cms"],
                "project_type": "application",
                "difficulty": "easy"
            },
            {
                "language": "Ruby",
                "topics": ["ruby", "rails", "web", "api"],
                "project_type": "application",
                "difficulty": "medium"
            },
            {
                "language": "Swift",
                "topics": ["swift", "ios", "mobile", "apple"],
                "project_type": "application",
                "difficulty": "medium"
            },
            {
                "language": "Kotlin",
                "topics": ["kotlin", "android", "mobile", "jvm"],
                "project_type": "application",
                "difficulty": "medium"
            },
            {
                "language": "Scala",
                "topics": ["scala", "jvm", "functional", "big-data"],
                "project_type": "library",
                "difficulty": "hard"
            },
            {
                "language": "C++",
                "topics": ["cpp", "systems", "performance", "game"],
                "project_type": "library",
                "difficulty": "hard"
            },
            {
                "language": "C",
                "topics": ["c", "systems", "embedded", "performance"],
                "project_type": "library",
                "difficulty": "hard"
            }
        ]
        
        category = random.choice(project_categories)
        
        return {
            "title": name.replace("-", " ").title(),
            "description": self._faker.sentence(),
            "short_description": self._faker.sentence(nb_words=10),
            "readme": self._faker.text(max_nb_chars=1000),
            "language": category["language"],
            "topics": category["topics"] + self._faker.words(nb=random.randint(1, 3)),
            "html_url": f"https://github.com/fake-org/{name}",
            "stargazers_count": self._faker.random_int(min=10, max=50000),
            "forks_count": self._faker.random_int(min=5, max=1000),
            "open_issues_count": self._faker.random_int(min=0, max=100),
            "pushed_at": datetime.utcnow(),
            "project_type": category["project_type"],
            "difficulty": category["difficulty"]
        }


class ProjectScraper:
    """Handles scraping and mapping of GitHub projects to database."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def scrape_and_populate(self, repo_file: str = None, num_projects: int = 10000, 
                          use_mock: bool = False):
        """Main method to scrape projects and populate database."""
        
        log.info("🚀 Starting project scraping and database population...")
        
        # Clear existing project data only
        self._clear_existing_project_data()
        
        # Fetch projects
        projects = self._fetch_projects(repo_file, num_projects, use_mock)
        
        # Create project roles (without users for now)
        roles = self._create_project_roles(projects)
        
        # Link projects to entities
        self._link_projects_to_entities(projects)
        
        # Create key features and project goals
        self._create_project_features_and_goals(projects)
        
        log.info("🎉 Project scraping completed successfully!")
        self._log_project_statistics()
    
    def _clear_existing_project_data(self):
        """Clear existing project data only."""
        log.info("Clearing existing project data...")
        
        # Delete in correct order to respect foreign key constraints
        self.db.query(ProjectRoleTechStack).delete()
        self.db.query(ProjectRole).delete()
        self.db.query(ProjectTechStack).delete()
        self.db.query(ProjectCategory).delete()
        self.db.query(KeyFeature).delete()
        self.db.query(ProjectGoal).delete()
        
        # Now safe to delete projects
        self.db.query(Project).delete()
        self.db.commit()
        
        log.info("✅ Cleared existing project data")
    
    def _fetch_projects(self, repo_file: str, num_projects: int, use_mock: bool):
        """Fetch projects from GitHub or use mock data."""
        log.info("Fetching projects...")
        
        gh_projects = []
        
        # Priority: 1. Repo file, 2. Environment variable, 3. Mock data
        if repo_file and os.path.exists(repo_file):
            log.info(f"Fetching repositories from file: {repo_file}...")
            with open(repo_file, "r") as f:
                repo_names = [line.strip() for line in f if line.strip()]
            
            if use_mock:
                log.info("Using MockGithubScraper for repository data...")
                scraper = MockGithubScraper()
                gh_projects = scraper.get_repositories_by_names(repo_names[:num_projects])
            else:
                log.info("Using real GithubScraper for repository data...")
                scraper = GithubScraper()
                gh_projects = scraper.get_repositories_by_names(repo_names[:num_projects])
        
        elif not use_mock:
            # Try environment variable
            repo_list_str = settings.GITHUB_REPO_LIST
            if repo_list_str:
                log.info("Fetching repositories from GITHUB_REPO_LIST variable...")
                scraper = GithubScraper()
                repo_names = [name.strip() for name in repo_list_str.split(",")]
                gh_projects = scraper.get_repositories_by_names(repo_names[:num_projects])
        
        # If still empty, use mock data
        if not gh_projects:
            log.info("No repository file found, using mock data...")
            scraper = MockGithubScraper()
            gh_projects = scraper.get_repositories("language:python", num_projects)

        if not gh_projects:
            log.warning("Could not fetch any projects from GitHub. Aborting population.")
            return []

        # Create a default owner for projects
        default_owner = User(
            username="github_owner",
            email="owner@github.com",
            login="github_owner",
            bio="Default owner for scraped projects",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(default_owner)
        self.db.flush()  # Get the ID without committing
        
        # Create Project objects
        projects = []
        for gh_project in gh_projects:
            project = Project(
                author_id=default_owner.id,
                title=gh_project["title"],
                description=gh_project["description"],
                short_description=gh_project.get("short_description", gh_project["description"][:100]),
                image=f"https://github.com/fake-org/{gh_project['title'].lower().replace(' ', '-')}/raw/main/screenshot.png",
                cover_images=f'["https://github.com/fake-org/{gh_project["title"].lower().replace(" ", "-")}/raw/main/cover1.png", "https://github.com/fake-org/{gh_project["title"].lower().replace(" ", "-")}/raw/main/cover2.png"]',
                readme=gh_project.get("readme", ""),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            projects.append(project)
        
        self.db.add_all(projects)
        self.db.commit()
        
        log.info(f"✅ Created {len(projects)} projects")
        return projects
    
    def _create_project_roles(self, projects: list):
        """Create project roles for each project."""
        log.info("Creating project roles...")
        
        roles = []
        for project in projects:
            # Create 1-3 fake roles for each project
            for i in range(random.randint(1, 3)):
                role = ProjectRole(
                    project_id=project.id,
                    title=f"Developer Role {i + 1}",
                    description=f"A sample description for role {i + 1} on project {project.title}.",
                    is_filled=random.choice([True, False]),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                roles.append(role)
        
        self.db.add_all(roles)
        self.db.commit()
        
        log.info(f"✅ Created {len(roles)} project roles")
        return roles
    
    def _link_projects_to_entities(self, projects: list):
        """Link projects to tech stacks and categories coherently."""
        log.info("Linking projects to entities...")
        
        tech_stacks = self.db.query(TechStack).all()
        categories = self.db.query(Category).all()
        
        if not tech_stacks or not categories:
            log.warning("Missing entities. Run simulate_projects.py first.")
            return
        
        project_tech_stacks = []
        project_categories = []
        project_role_tech_stacks = []
        
        for project in projects:
            # Link based on project description and random assignment
            # We'll use project description and random assignment for now
            if "python" in project.description.lower() or "data" in project.description.lower():
                # Python/Data projects
                matching_techs = [t for t in tech_stacks if t.name in ["Python", "Pandas", "PostgreSQL", "GitHub"]]
                matching_categories = [c for c in categories if c.name in ["Data Science", "AI/ML", "DevTools"]]
            elif "react" in project.description.lower() or "frontend" in project.description.lower():
                # Frontend projects
                matching_techs = [t for t in tech_stacks if t.name in ["React", "Vue.js", "TypeScript", "CSS", "HTML"]]
                matching_categories = [c for c in categories if c.name in ["Web Development", "Social", "E-commerce"]]
            elif "mobile" in project.description.lower() or "app" in project.description.lower():
                # Mobile projects
                matching_techs = [t for t in tech_stacks if t.name in ["React Native", "Flutter", "Swift", "Kotlin"]]
                matching_categories = [c for c in categories if c.name in ["Mobile Development", "Gaming", "Social"]]
            elif "backend" in project.description.lower() or "api" in project.description.lower():
                # Backend projects
                matching_techs = [t for t in tech_stacks if t.name in ["Node.js", "Java", "Go", "PostgreSQL", "Docker"]]
                matching_categories = [c for c in categories if c.name in ["DevTools", "Finance", "E-commerce"]]
            else:
                # Default projects
                matching_techs = [t for t in tech_stacks if t.name in ["Python", "Git", "GitHub"]]
                matching_categories = [c for c in categories if c.name in ["DevTools", "Web Development"]]
            
            # Add primary tech stacks and categories
            for tech in matching_techs[:3]:  # Limit to 3 primary techs
                project_tech_stacks.append(ProjectTechStack(
                    project_id=project.id,
                    tech_stack_id=tech.id
                ))
            
            for category in matching_categories[:2]:  # Limit to 2 primary categories
                project_categories.append(ProjectCategory(
                    project_id=project.id,
                    category_id=category.id
                ))
            
            # Add some random secondary links
            num_secondary_techs = min(random.randint(1, 3), len(tech_stacks))
            num_secondary_categories = min(random.randint(1, 2), len(categories))
            
            secondary_techs = random.sample(tech_stacks, num_secondary_techs)
            secondary_categories = random.sample(categories, num_secondary_categories)
            
            project_tech_stacks.extend([
                ProjectTechStack(project_id=project.id, tech_stack_id=t.id)
                for t in secondary_techs
            ])
            project_categories.extend([
                ProjectCategory(project_id=project.id, category_id=c.id)
                for c in secondary_categories
            ])
            
            # Link project roles to tech stacks
            project_roles = self.db.query(ProjectRole).filter_by(project_id=project.id).all()
            for role in project_roles:
                role_techs = random.sample(matching_techs, min(2, len(matching_techs)))
                for tech in role_techs:
                    project_role_tech_stacks.append(ProjectRoleTechStack(
                        project_role_id=role.id,
                        tech_stack_id=tech.id
                    ))
        
        self.db.add_all(project_tech_stacks)
        self.db.add_all(project_categories)
        self.db.add_all(project_role_tech_stacks)
        self.db.commit()
        
        log.info(f"Linked {len(project_tech_stacks)} tech stacks, {len(project_categories)} categories, {len(project_role_tech_stacks)} role tech stacks to projects")
    
    def _create_project_features_and_goals(self, projects: list):
        """Create key features and project goals for projects."""
        log.info("Creating key features and project goals...")
        
        key_features = []
        project_goals = []
        
        feature_templates = [
            "User authentication and authorization",
            "Real-time data processing",
            "Responsive design for mobile devices",
            "API integration with third-party services",
            "Advanced search and filtering",
            "Data visualization and analytics",
            "Automated testing and CI/CD",
            "Scalable microservices architecture",
            "Real-time notifications",
            "Multi-language support",
            "Advanced caching system",
            "Security and encryption",
            "Performance optimization",
            "Accessibility compliance",
            "Cross-platform compatibility"
        ]
        
        goal_templates = [
            "Improve user experience and interface design",
            "Enhance performance and scalability",
            "Increase code quality and maintainability",
            "Add new features and functionality",
            "Improve security and data protection",
            "Optimize for mobile devices",
            "Implement automated testing",
            "Reduce technical debt",
            "Enhance documentation",
            "Improve accessibility",
            "Add internationalization support",
            "Implement monitoring and logging",
            "Optimize database queries",
            "Add real-time capabilities",
            "Improve error handling"
        ]
        
        for project in projects:
            # Create 2-4 key features per project
            num_features = random.randint(2, 4)
            selected_features = random.sample(feature_templates, num_features)
            
            for feature in selected_features:
                key_features.append(KeyFeature(
                    project_id=project.id,
                    feature=feature
                ))
            
            # Create 1-3 project goals per project
            num_goals = random.randint(1, 3)
            selected_goals = random.sample(goal_templates, num_goals)
            
            for goal in selected_goals:
                project_goals.append(ProjectGoal(
                    project_id=project.id,
                    goal=goal
                ))
        
        self.db.add_all(key_features)
        self.db.add_all(project_goals)
        self.db.commit()
        
        log.info(f"✅ Created {len(key_features)} key features and {len(project_goals)} project goals")
    
    def _log_project_statistics(self):
        """Log project statistics only."""
        log.info("📊 Project Statistics:")
        log.info(f"   Total Projects: {self.db.query(Project).count()}")
        log.info(f"   Total Project Roles: {self.db.query(ProjectRole).count()}")
        log.info(f"   Total Project-TechStack links: {self.db.query(ProjectTechStack).count()}")
        log.info(f"   Total Project-Category links: {self.db.query(ProjectCategory).count()}")
        log.info(f"   Total ProjectRole-TechStack links: {self.db.query(ProjectRoleTechStack).count()}")
        log.info(f"   Total Key Features: {self.db.query(KeyFeature).count()}")
        log.info(f"   Total Project Goals: {self.db.query(ProjectGoal).count()}")


def main():
    """Main function to run the scraping and population process."""
    parser = argparse.ArgumentParser(
        description="Scrape GitHub repositories and populate the database with project data."
    )
    parser.add_argument(
        "--repo-file",
        type=str,
        default=None,
        help="Path to a file containing a list of repositories to scrape (one per line).",
    )
    parser.add_argument(
        "--num-projects",
        type=int,
        default=10000,
        help="Number of projects to fetch and populate (default: 10000).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of fetching from GitHub API.",
    )

    
    args = parser.parse_args()

    log.info("🚀 Starting project scraping and database population...")
    
    db_session = SessionLocal()
    try:
        scraper = ProjectScraper(db_session)
        scraper.scrape_and_populate(
            repo_file=args.repo_file,
            num_projects=args.num_projects,
            use_mock=args.mock
        )
    finally:
        db_session.close()
        log.info("Script finished. Database session closed.")


if __name__ == "__main__":
    main() 