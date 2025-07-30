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
    ProjectSkill,
    ProjectTechnology,
    ProjectDomainCategory,
    ProjectRoleSkill,
    ProjectRoleTechnology,
    IssueSkill,
    IssueTechnology,
    LinkedRepository,
    GoodFirstIssue,
    Skill,
    Technology,
    DomainCategory,
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
        
        log.info("🎉 Project scraping completed successfully!")
        self._log_project_statistics()
    
    def _clear_existing_project_data(self):
        """Clear existing project data only."""
        log.info("Clearing existing project data...")
        
        # Delete in correct order to respect foreign key constraints
        self.db.query(ProjectRole).delete()
        
        # Clear project-entity linking tables
        self.db.query(ProjectSkill).delete()
        self.db.query(ProjectTechnology).delete()
        self.db.query(ProjectDomainCategory).delete()
        self.db.query(ProjectRoleSkill).delete()
        self.db.query(ProjectRoleTechnology).delete()
        self.db.query(IssueSkill).delete()
        self.db.query(IssueTechnology).delete()
        self.db.query(LinkedRepository).delete()
        self.db.query(GoodFirstIssue).delete()
        
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
            bio="Default owner for scraped projects",
            github_username="github_owner",
            level="advanced"
        )
        self.db.add(default_owner)
        self.db.flush()  # Get the ID without committing
        
        # Create Project objects (UPDATED - removed legacy fields)
        projects = []
        for gh_project in gh_projects:
            project = Project(
                title=gh_project["title"],
                description=gh_project["description"],
                # REMOVED: readme, language, topics, forks_count, open_issues_count, pushed_at
                github_main_repo=gh_project.get("html_url", None),
                stars_count=gh_project["stargazers_count"],
                owner_id=default_owner.id,  # Use default owner
                status="active",
                is_seeking_contributors=True,
                project_type=gh_project.get("project_type", "library"),
                difficulty=gh_project.get("difficulty", "medium"),
                license=random.choice(["MIT", "Apache-2.0", "GPL-3.0", "custom", "other"])
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
                    responsibility_level=random.choice(["contributor", "maintainer", "lead"]),
                    time_commitment=random.choice(["few_hours", "part_time", "full_time"]),
                    slots_available=random.randint(1, 3),
                    slots_filled=0,
                    experience_required=random.choice(["none", "some", "experienced"])
                )
                roles.append(role)
        
        self.db.add_all(roles)
        self.db.commit()
        
        log.info(f"✅ Created {len(roles)} project roles")
        return roles
    

    
    def _link_projects_to_entities(self, projects: list):
        """Link projects to skills, technologies, and domains coherently."""
        log.info("Linking projects to entities...")
        
        skills = self.db.query(Skill).all()
        technologies = self.db.query(Technology).all()
        domains = self.db.query(DomainCategory).all()
        
        if not skills or not technologies or not domains:
            log.warning("Missing entities. Run create_tables.py first.")
            return
        
        project_skills = []
        project_technologies = []
        project_domains = []
        
        for project in projects:
            # Link based on project type and random assignment (since we removed language field)
            # We'll use project_type and random assignment for now
            if project.project_type == "library":
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Python", "Data Analysis", "Machine Learning", "Systems Programming"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Python", "Docker", "GitHub", "Git"]
                ])
            elif project.project_type == "application":
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["React", "Vue.js", "TypeScript", "Web Development", "Mobile Development"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["React", "Vue.js", "TypeScript", "Node.js", "GitHub"]
                ])
            elif project.project_type == "tool":
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Go", "API Design", "Database Design", "Systems Programming"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Go", "Docker", "Kubernetes", "GitHub"]
                ])
            elif project.project_type == "framework":
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Java", "Spring Boot", "API Design", "Web Development"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Java", "Spring Boot", "Maven", "GitHub"]
                ])
            else:  # "other" or default
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Python", "Web Development", "API Design"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Python", "Git", "GitHub"]
                ])
            
            # Add some random secondary links
            num_secondary_skills = min(random.randint(1, 3), len(skills))
            num_secondary_techs = min(random.randint(1, 3), len(technologies))
            num_domains = min(random.randint(1, 2), len(domains))
            
            secondary_skills = random.sample(skills, num_secondary_skills)
            secondary_techs = random.sample(technologies, num_secondary_techs)
            selected_domains = random.sample(domains, num_domains)
            
            project_skills.extend([
                ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=False)
                for s in secondary_skills
            ])
            project_technologies.extend([
                ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=False)
                for t in secondary_techs
            ])
            project_domains.extend([
                ProjectDomainCategory(project_id=project.id, domain_category_id=d.id, is_primary=False)
                for d in selected_domains
            ])
        
        self.db.add_all(project_skills)
        self.db.add_all(project_technologies)
        self.db.add_all(project_domains)
        self.db.commit()
        
        log.info(f"Linked {len(project_skills)} skills, {len(project_technologies)} technologies, {len(project_domains)} domains to projects")
    

    
    def _log_project_statistics(self):
        """Log project statistics only."""
        log.info("📊 Project Statistics:")
        log.info(f"   Total Projects: {self.db.query(Project).count()}")
        log.info(f"   Total Project Roles: {self.db.query(ProjectRole).count()}")
        log.info(f"   Total Project-Skill links: {self.db.query(ProjectSkill).count()}")
        log.info(f"   Total Project-Technology links: {self.db.query(ProjectTechnology).count()}")
        log.info(f"   Total Project-Domain links: {self.db.query(ProjectDomainCategory).count()}")


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