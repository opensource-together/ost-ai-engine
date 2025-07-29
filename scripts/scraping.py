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
    Application,
    Base,
    Contribution,
    Project,
    ProjectRole,
    TeamMember,
    User,
    UserSkill,
    UserTechnology,
    CommunityMember,
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
)
from src.infrastructure.config import settings
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import SessionLocal, engine
from src.infrastructure.scraping.github_scraper import GithubScraper


class CoherentDataGenerator:
    """Generate coherent user-project interactions based on skills and interests."""
    
    def __init__(self):
        self._faker = Faker()
        
        # Define skill-technology mappings for coherence
        self.skill_tech_mapping = {
            # Frontend Development
            "React": ["React", "JavaScript", "TypeScript", "CSS", "HTML", "Redux", "Next.js", "Material-UI"],
            "Vue.js": ["Vue.js", "JavaScript", "TypeScript", "CSS", "HTML", "Vuex", "Nuxt.js", "Vuetify"],
            "Angular": ["Angular", "TypeScript", "JavaScript", "CSS", "HTML", "RxJS", "Angular Material"],
            "TypeScript": ["TypeScript", "JavaScript", "React", "Vue.js", "Angular", "Node.js"],
            "CSS": ["CSS", "Sass", "Less", "Tailwind CSS", "Bootstrap", "HTML"],
            "HTML": ["HTML", "CSS", "JavaScript", "Semantic HTML", "Accessibility"],
            
            # Backend Development
            "Python": ["Python", "Django", "Flask", "FastAPI", "Pandas", "NumPy", "SQLAlchemy", "Celery"],
            "Node.js": ["Node.js", "JavaScript", "Express.js", "NestJS", "Socket.io", "PM2"],
            "Java": ["Java", "Spring Boot", "Spring Security", "Maven", "Gradle", "JUnit"],
            "Go": ["Go", "Gin", "Echo", "Docker", "Kubernetes", "Microservices"],
            "C#": ["C#", ".NET", "ASP.NET Core", "Entity Framework", "LINQ", "Visual Studio"],
            "PHP": ["PHP", "Laravel", "Symfony", "WordPress", "Composer", "MySQL"],
            "Ruby": ["Ruby", "Ruby on Rails", "Sinatra", "RSpec", "Bundler"],
            
            # Database & ORM
            "PostgreSQL": ["PostgreSQL", "SQL", "Python", "Node.js", "Django", "Sequelize"],
            "MySQL": ["MySQL", "SQL", "PHP", "Laravel", "WordPress", "Node.js"],
            "MongoDB": ["MongoDB", "NoSQL", "Node.js", "Mongoose", "Python", "PyMongo"],
            "Redis": ["Redis", "Caching", "Node.js", "Python", "Session Management"],
            
            # DevOps & Infrastructure
            "Docker": ["Docker", "Containerization", "Kubernetes", "CI/CD", "DevOps"],
            "Kubernetes": ["Kubernetes", "Container Orchestration", "Docker", "Helm", "Microservices"],
            "AWS": ["AWS", "Cloud Computing", "EC2", "S3", "Lambda", "RDS", "DevOps"],
            "Azure": ["Azure", "Cloud Computing", "DevOps", "C#", ".NET", "PowerShell"],
            "GCP": ["GCP", "Cloud Computing", "Kubernetes", "BigQuery", "DevOps"],
            "Terraform": ["Terraform", "Infrastructure as Code", "AWS", "Azure", "GCP"],
            "Jenkins": ["Jenkins", "CI/CD", "DevOps", "Automation", "Pipeline"],
            "GitHub Actions": ["GitHub Actions", "CI/CD", "DevOps", "Automation"],
            
            # Data Science & ML
            "Machine Learning": ["Python", "Scikit-learn", "TensorFlow", "PyTorch", "Pandas", "NumPy"],
            "Data Analysis": ["Python", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter"],
            "Deep Learning": ["Python", "TensorFlow", "PyTorch", "Keras", "GPU Computing"],
            "NLP": ["Python", "NLTK", "spaCy", "Transformers", "BERT", "GPT"],
            "Computer Vision": ["Python", "OpenCV", "TensorFlow", "PyTorch", "Image Processing"],
            
            # Mobile Development
            "React Native": ["React Native", "JavaScript", "React", "Mobile Development", "iOS", "Android"],
            "Flutter": ["Flutter", "Dart", "Mobile Development", "iOS", "Android", "Cross-platform"],
            "iOS Development": ["Swift", "Objective-C", "Xcode", "iOS", "Mobile Development", "UIKit"],
            "Android Development": ["Kotlin", "Java", "Android Studio", "Android", "Mobile Development"],
            
            # Testing & Quality
            "Unit Testing": ["Jest", "JUnit", "PyTest", "Mocha", "Testing", "TDD"],
            "Integration Testing": ["Postman", "Newman", "API Testing", "End-to-End Testing"],
            "E2E Testing": ["Cypress", "Selenium", "Playwright", "End-to-End Testing"],
            
            # Design & UX
            "UI Design": ["Figma", "Adobe XD", "Sketch", "InVision", "Prototyping", "Design Systems"],
            "UX Design": ["Figma", "User Research", "Usability Testing", "Wireframing", "Prototyping"],
            "Graphic Design": ["Adobe Photoshop", "Adobe Illustrator", "InDesign", "Creative Suite"],
            
            # Security
            "Cybersecurity": ["Security", "Penetration Testing", "OWASP", "Authentication", "Authorization"],
            "Authentication": ["OAuth", "JWT", "OpenID Connect", "Security", "Identity Management"],
            
            # Blockchain & Web3
            "Blockchain": ["Solidity", "Ethereum", "Web3", "Smart Contracts", "DApps"],
            "Web3": ["Web3", "Ethereum", "Solidity", "MetaMask", "DApps"],
            
            # Game Development
            "Game Development": ["Unity", "C#", "Unreal Engine", "C++", "Game Design"],
            "Unity": ["Unity", "C#", "Game Development", "3D Graphics", "Game Design"],
            
            # AI & Automation
            "AI": ["Python", "Machine Learning", "Deep Learning", "NLP", "Computer Vision"],
            "RPA": ["Automation", "UiPath", "Blue Prism", "Process Automation"],
            
            # Communication & Collaboration
            "Slack": ["Slack", "Communication", "Team Collaboration", "API Integration"],
            "Discord": ["Discord", "Communication", "Bot Development", "API Integration"],
            "Notion": ["Notion", "Documentation", "Project Management", "Knowledge Base"],
            
            # Version Control & Git
            "Git": ["Git", "GitHub", "GitLab", "Version Control", "Collaboration"],
            "GitHub": ["GitHub", "Git", "Version Control", "CI/CD", "Open Source"],
        }
        
        # Define domain interest patterns
        self.domain_patterns = {
            # Frontend Development
            "React": ["E-commerce", "Social", "Productivity", "Education", "Entertainment"],
            "Vue.js": ["E-commerce", "Social", "Productivity", "Education", "Business"],
            "Angular": ["Enterprise", "Business", "Finance", "Healthcare", "Education"],
            "TypeScript": ["Enterprise", "Business", "Finance", "DevTools", "Productivity"],
            "CSS": ["Design", "E-commerce", "Social", "Entertainment", "Education"],
            "HTML": ["Web Development", "E-commerce", "Social", "Education", "Business"],
            
            # Backend Development
            "Python": ["Data Science", "Finance", "Healthcare", "Education", "DevTools", "E-commerce"],
            "Node.js": ["Social", "E-commerce", "Entertainment", "Productivity", "DevTools"],
            "Java": ["Enterprise", "Finance", "Healthcare", "Government", "Education"],
            "Go": ["DevTools", "Infrastructure", "Finance", "Microservices", "Cloud"],
            "C#": ["Enterprise", "Gaming", "Healthcare", "Finance", "Government"],
            "PHP": ["E-commerce", "Social", "CMS", "Business", "Education"],
            "Ruby": ["Startups", "E-commerce", "Social", "Productivity", "Education"],
            
            # Database & ORM
            "PostgreSQL": ["Enterprise", "Finance", "Healthcare", "E-commerce", "Analytics"],
            "MySQL": ["E-commerce", "CMS", "Social", "Business", "Education"],
            "MongoDB": ["Social", "Content Management", "Analytics", "IoT", "Mobile"],
            "Redis": ["Caching", "Session Management", "Real-time", "Social", "Gaming"],
            
            # DevOps & Infrastructure
            "Docker": ["DevOps", "Cloud", "Microservices", "CI/CD", "Infrastructure"],
            "Kubernetes": ["Cloud", "Microservices", "DevOps", "Infrastructure", "Enterprise"],
            "AWS": ["Cloud", "Enterprise", "Startups", "DevOps", "Infrastructure"],
            "Azure": ["Enterprise", "Cloud", "Government", "Healthcare", "Finance"],
            "GCP": ["Cloud", "Data Science", "AI/ML", "Analytics", "Enterprise"],
            "Terraform": ["DevOps", "Infrastructure", "Cloud", "Automation", "Enterprise"],
            "Jenkins": ["DevOps", "CI/CD", "Automation", "Enterprise", "Infrastructure"],
            "GitHub Actions": ["DevOps", "CI/CD", "Open Source", "Automation", "Collaboration"],
            
            # Data Science & ML
            "Machine Learning": ["Finance", "Healthcare", "E-commerce", "Education", "Research"],
            "Data Analysis": ["Finance", "Healthcare", "E-commerce", "Education", "Business"],
            "Deep Learning": ["AI/ML", "Computer Vision", "NLP", "Research", "Healthcare"],
            "NLP": ["AI/ML", "Social", "Customer Service", "Education", "Healthcare"],
            "Computer Vision": ["AI/ML", "Healthcare", "Security", "Automotive", "Retail"],
            
            # Mobile Development
            "React Native": ["Social", "E-commerce", "Entertainment", "Productivity", "Education"],
            "Flutter": ["Social", "E-commerce", "Entertainment", "Productivity", "Education"],
            "iOS Development": ["Social", "Entertainment", "Productivity", "Education", "Healthcare"],
            "Android Development": ["Social", "Entertainment", "Productivity", "Education", "Business"],
            
            # Testing & Quality
            "Unit Testing": ["Quality Assurance", "DevOps", "Enterprise", "Finance", "Healthcare"],
            "Integration Testing": ["Quality Assurance", "DevOps", "Enterprise", "API Development"],
            "E2E Testing": ["Quality Assurance", "E-commerce", "Social", "Enterprise", "Healthcare"],
            
            # Design & UX
            "UI Design": ["E-commerce", "Social", "Entertainment", "Education", "Productivity"],
            "UX Design": ["E-commerce", "Social", "Healthcare", "Education", "Productivity"],
            "Graphic Design": ["Marketing", "Entertainment", "E-commerce", "Education", "Media"],
            
            # Security
            "Cybersecurity": ["Finance", "Healthcare", "Government", "Enterprise", "Infrastructure"],
            "Authentication": ["Enterprise", "Finance", "Healthcare", "Social", "E-commerce"],
            
            # Blockchain & Web3
            "Blockchain": ["Finance", "Gaming", "Social", "Supply Chain", "Identity"],
            "Web3": ["Finance", "Gaming", "Social", "Art", "Identity"],
            
            # Game Development
            "Game Development": ["Gaming", "Entertainment", "Education", "Social", "VR/AR"],
            "Unity": ["Gaming", "Entertainment", "Education", "VR/AR", "Simulation"],
            
            # AI & Automation
            "AI": ["Finance", "Healthcare", "E-commerce", "Education", "Automation"],
            "RPA": ["Enterprise", "Finance", "Healthcare", "Manufacturing", "Automation"],
            
            # Communication & Collaboration
            "Slack": ["Communication", "Enterprise", "Startups", "Remote Work", "Collaboration"],
            "Discord": ["Gaming", "Social", "Education", "Entertainment", "Community"],
            "Notion": ["Productivity", "Education", "Business", "Documentation", "Collaboration"],
            
            # Version Control & Git
            "Git": ["Development", "Collaboration", "Open Source", "DevOps", "Version Control"],
            "GitHub": ["Open Source", "Collaboration", "Development", "DevOps", "Community"],
        }
    
    def create_coherent_user_profile(self, user_id: str, skill_category: str) -> dict:
        """Create a user profile with coherent skills and interests."""
        
        # Get the skill-technology mapping for this category
        if skill_category in self.skill_tech_mapping:
            technologies = self.skill_tech_mapping[skill_category]
            # Use the main skill as the primary skill
            skills = [skill_category] + [tech for tech in technologies if tech != skill_category][:5]
        else:
            # Fallback for unknown categories
            skills = [skill_category]
            technologies = [skill_category]
        
        # Get domain patterns for this category
        if skill_category in self.domain_patterns:
            domains = self.domain_patterns[skill_category]
        else:
            # Fallback domains
            domains = ["Education", "E-commerce", "Social"]
        
        return {
            "user_id": user_id,
            "skills": skills,
            "technologies": technologies,
            "domains": domains,
            "category": skill_category
        }
    
    def find_matching_projects(self, user_profile: dict, projects: list, db: Session) -> list:
        """Find projects that match user's skills and interests."""
        
        matching_projects = []
        user_skills = set(user_profile["skills"])
        user_technologies = set(user_profile["technologies"])
        user_domains = set(user_profile["domains"])
        
        for project in projects:
            # Get project skills and technologies
            project_skills = db.query(ProjectSkill).filter_by(project_id=project.id).all()
            project_technologies = db.query(ProjectTechnology).filter_by(project_id=project.id).all()
            project_domains = db.query(ProjectDomainCategory).filter_by(project_id=project.id).all()
            
            # Calculate match score
            skill_matches = sum(1 for ps in project_skills if ps.skill.name in user_skills)
            tech_matches = sum(1 for pt in project_technologies if pt.technology.name in user_technologies)
            domain_matches = sum(1 for pd in project_domains if pd.domain_category.name in user_domains)
            
            # Project matches if it has at least 2 matching criteria
            if skill_matches + tech_matches + domain_matches >= 2:
                matching_projects.append(project)
        
        # If no perfect matches, return some random projects but with bias
        if not matching_projects:
            return random.sample(projects, min(10, len(projects)))
        
        return matching_projects
    
    def simulate_coherent_interactions(self, user_profile: dict, matching_projects: list, 
                                    num_interactions: int, db: Session) -> list:
        """Simulate interactions that make sense for the user's profile."""
        
        interactions = []
        user_id = user_profile["user_id"]
        category = user_profile["category"]
        
        # Weight interactions based on user category
        if category == "Frontend":
            weights = {"contribution": 0.4, "application": 0.4, "member": 0.2}
        elif category == "Backend":
            weights = {"contribution": 0.5, "application": 0.3, "member": 0.2}
        elif category == "Mobile":
            weights = {"contribution": 0.3, "application": 0.5, "member": 0.2}
        elif category == "Data Science":
            weights = {"contribution": 0.6, "application": 0.2, "member": 0.2}
        else:  # DevOps
            weights = {"contribution": 0.4, "application": 0.3, "member": 0.3}
        
        for _ in range(num_interactions):
            project = random.choice(matching_projects)
            action_type = random.choices(
                list(weights.keys()), 
                weights=list(weights.values())
            )[0]
            
            if action_type == "contribution":
                # Frontend users more likely to contribute design/code
                if category == "Frontend":
                    contrib_type = random.choice(["design", "code", "documentation"])
                elif category == "Data Science":
                    contrib_type = random.choice(["code", "bug_fix", "feature"])
                else:
                    contrib_type = random.choice(["code", "bug_fix", "feature", "documentation"])
                
                interactions.append(Contribution(
                    user_id=user_id,
                    project_id=project.id,
                    type=contrib_type,
                    title=f"Contribution to {project.title}",
                    description=f"User contribution to {project.title}",
                    status=random.choice(["submitted", "reviewed", "merged"])
                ))
            
            elif action_type == "application":
                # Get project roles for this project
                project_roles = db.query(ProjectRole).filter_by(project_id=project.id).all()
                if project_roles:
                    role = random.choice(project_roles)
                    interactions.append(Application(
                        user_id=user_id,
                        project_role_id=role.id,
                        portfolio_links='["https://github.com/user", "https://linkedin.com/user"]',
                        availability=random.choice(["immediate", "within_week", "within_month"]),
                        status=random.choice(["pending", "accepted", "rejected"])
                    ))
            
            elif action_type == "member":
                project_roles = db.query(ProjectRole).filter_by(project_id=project.id).all()
                if project_roles:
                    role = random.choice(project_roles)
                    interactions.append(TeamMember(
                        user_id=user_id,
                        project_id=project.id,
                        project_role_id=role.id,
                        status="active",
                        contributions_count=random.randint(1, 10)
                    ))
        
        return interactions


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
            "stargazers_count": self._faker.random_int(min=10, max=5000),
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
        self.generator = CoherentDataGenerator()
    
    def scrape_and_populate(self, repo_file: str = None, num_projects: int = 5000, 
                          use_mock: bool = False, num_users: int = 50, num_actions: int = 1000):
        """Main method to scrape projects and populate database."""
        
        log.info("🚀 Starting project scraping and database population...")
        
        # Clear existing data
        self._clear_existing_data()
        
        # Create users with coherent profiles
        users, user_profiles = self._create_users_with_profiles(num_users)
        
        # Fetch projects
        projects = self._fetch_projects(repo_file, num_projects, use_mock)
        
        # Create project roles
        roles = self._create_project_roles(projects, users)
        
        # Create coherent user interactions
        self._create_coherent_interactions(users, user_profiles, projects, num_actions)
        
        # Link projects to entities
        self._link_projects_to_entities(projects)
        
        # Create user skills and technologies
        self._create_user_profiles_coherent(users, user_profiles)
        
        log.info("🎉 Database population completed successfully!")
        self._log_statistics()
    
    def _clear_existing_data(self):
        """Clear existing data from tables we'll populate."""
        log.info("Clearing existing data...")
        
        # Delete in correct order to respect foreign key constraints
        self.db.query(Application).delete()
        self.db.query(Contribution).delete()
        self.db.query(TeamMember).delete()
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
        
        # Clear user-related data
        self.db.query(UserSkill).delete()
        self.db.query(UserTechnology).delete()
        self.db.query(CommunityMember).delete()
        
        # Now safe to delete users
        self.db.query(User).delete()
        self.db.commit()
        
        log.info("✅ Cleared existing data")
    
    def _create_users_with_profiles(self, num_users: int):
        """Create users with coherent profiles."""
        log.info(f"Creating {num_users} users with coherent profiles...")
        
        user_categories = [
            "React", "Vue.js", "Angular", "TypeScript", "Python", "Node.js", "Java", "Go", 
            "C#", "PHP", "PostgreSQL", "MySQL", "Docker", "Kubernetes", "AWS", "Machine Learning", 
            "Data Analysis", "React Native", "Flutter", "UI Design", "UX Design", "Git", "GitHub"
        ]
        
        users = []
        user_profiles = []
        
        for i in range(num_users):
            category = random.choice(user_categories)
            user = User(
                username=f"user_{category.lower()}_{i}",
                email=f"user_{category.lower()}_{i}@example.com"
            )
            users.append(user)
            
            profile = self.generator.create_coherent_user_profile(str(user.id), category)
            user_profiles.append(profile)
        
        self.db.add_all(users)
        self.db.commit()
        
        log.info(f"✅ Created {len(users)} users with profiles")
        return users, user_profiles
    
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

        # Create Project objects
        projects = []
        for gh_project in gh_projects:
            # Get a random user as owner
            owner = random.choice(self.db.query(User).all()) if self.db.query(User).count() > 0 else None
            
            project = Project(
                title=gh_project["title"],
                description=gh_project["description"],
                readme=gh_project["readme"],
                language=gh_project["language"],
                topics=",".join(gh_project["topics"]),
                github_main_repo=gh_project.get("html_url", None),
                stars_count=gh_project["stargazers_count"],
                forks_count=gh_project["forks_count"],
                open_issues_count=gh_project["open_issues_count"],
                pushed_at=gh_project["pushed_at"],
                owner_id=owner.id if owner else None,
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
    
    def _create_project_roles(self, projects: list, users: list):
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
    
    def _create_coherent_interactions(self, users: list, user_profiles: list, 
                                   projects: list, num_actions: int):
        """Create coherent user interactions."""
        log.info("Creating coherent user interactions...")
        
        all_interactions = []
        team_member_cache = set()
        application_cache = set()

        for user, profile in zip(users, user_profiles):
            # Find projects that match user's profile
            matching_projects = self.generator.find_matching_projects(profile, projects, self.db)
            
            # Update profile with actual user.id
            profile["user_id"] = user.id
            
            # Generate coherent interactions for this user
            user_interactions = self.generator.simulate_coherent_interactions(
                profile, matching_projects, num_actions // len(users), self.db
            )
            
            # Add to global interactions list
            for interaction in user_interactions:
                if isinstance(interaction, TeamMember):
                    if (user.id, interaction.project_id) not in team_member_cache:
                        all_interactions.append(interaction)
                        team_member_cache.add((user.id, interaction.project_id))
                elif isinstance(interaction, Application):
                    if (user.id, interaction.project_role_id) not in application_cache:
                        all_interactions.append(interaction)
                        application_cache.add((user.id, interaction.project_role_id))
                else:
                    all_interactions.append(interaction)

        self.db.add_all(all_interactions)
        self.db.commit()
        
        log.info(f"✅ Created {len(all_interactions)} coherent interactions")
    
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
            # Link based on project language and type
            if "Python" in project.language:
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Python", "Data Analysis", "Machine Learning"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Python", "Docker", "GitHub"]
                ])
            elif "JavaScript" in project.language:
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["React", "Vue.js", "TypeScript"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["React", "Vue.js", "TypeScript", "Node.js"]
                ])
            elif "Go" in project.language:
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Go", "API Design", "Database Design"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Go", "Docker", "Kubernetes"]
                ])
            elif "Rust" in project.language:
                project_skills.extend([
                    ProjectSkill(project_id=project.id, skill_id=s.id, is_primary=True)
                    for s in skills if s.name in ["Rust", "Systems Programming"]
                ])
                project_technologies.extend([
                    ProjectTechnology(project_id=project.id, technology_id=t.id, is_primary=True)
                    for t in technologies if t.name in ["Rust", "Git", "GitHub"]
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
    
    def _create_user_profiles_coherent(self, users: list, user_profiles: list):
        """Create user skills and technologies based on their coherent profiles."""
        log.info("Creating coherent user profiles...")
        
        skills = self.db.query(Skill).all()
        technologies = self.db.query(Technology).all()
        
        if not skills or not technologies:
            log.warning("Missing skills or technologies. Run create_tables.py first.")
            return
        
        user_skills = []
        user_technologies = []
        
        for user, profile in zip(users, user_profiles):
            # Create skills based on profile
            for skill_name in profile["skills"]:
                skill = next((s for s in skills if s.name == skill_name), None)
                if skill:
                    user_skills.append(UserSkill(
                        user_id=user.id,
                        skill_id=skill.id,
                        proficiency_level=random.choice(["basic", "intermediate", "advanced"]),
                        is_primary=True
                    ))
            
            # Create technologies based on profile
            for tech_name in profile["technologies"]:
                tech = next((t for t in technologies if t.name == tech_name), None)
                if tech:
                    user_technologies.append(UserTechnology(
                        user_id=user.id,
                        technology_id=tech.id,
                        proficiency_level=random.choice(["basic", "intermediate", "advanced"]),
                        is_primary=True
                    ))
        
        self.db.add_all(user_skills)
        self.db.add_all(user_technologies)
        self.db.commit()
        
        log.info(f"Created {len(user_skills)} coherent user skills and {len(user_technologies)} user technologies")
    
    def _log_statistics(self):
        """Log final statistics."""
        log.info("📊 Final Statistics:")
        log.info(f"   Total Users: {self.db.query(User).count()}")
        log.info(f"   Total Projects: {self.db.query(Project).count()}")
        log.info(f"   Total Team Memberships: {self.db.query(TeamMember).count()}")
        log.info(f"   Total Contributions: {self.db.query(Contribution).count()}")
        log.info(f"   Total Applications: {self.db.query(Application).count()}")
        log.info(f"   Total Project-Skill links: {self.db.query(ProjectSkill).count()}")
        log.info(f"   Total Project-Technology links: {self.db.query(ProjectTechnology).count()}")
        log.info(f"   Total User-Skill links: {self.db.query(UserSkill).count()}")
        log.info(f"   Total User-Technology links: {self.db.query(UserTechnology).count()}")


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
        default=5000,
        help="Number of projects to fetch and populate (default: 5000).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of fetching from GitHub API.",
    )
    parser.add_argument(
        "--num-users",
        type=int,
        default=50,
        help="Number of users to create (default: 50).",
    )
    parser.add_argument(
        "--num-actions",
        type=int,
        default=1000,
        help="Number of user actions to simulate (default: 1000).",
    )
    
    args = parser.parse_args()

    log.info("🚀 Starting project scraping and database population...")
    
    db_session = SessionLocal()
    try:
        scraper = ProjectScraper(db_session)
        scraper.scrape_and_populate(
            repo_file=args.repo_file,
            num_projects=args.num_projects,
            use_mock=args.mock,
            num_users=args.num_users,
            num_actions=args.num_actions
        )
    finally:
        db_session.close()
        log.info("Script finished. Database session closed.")


if __name__ == "__main__":
    main() 