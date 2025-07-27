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
    Skill,
    Technology,
    DomainCategory,
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
        """Generates a single fake project dictionary."""
        return {
            "title": name.replace("-", " ").title(),
            "description": self._faker.sentence(),
            "readme": self._faker.text(max_nb_chars=1000),
            "language": self._faker.random_element(
                elements=("Python", "JavaScript", "TypeScript", "Go", "Rust")
            ),
            "topics": self._faker.words(nb=random.randint(3, 7)),
            "html_url": f"https://github.com/fake-org/{name}",
            "stargazers_count": self._faker.random_int(min=10, max=5000),
            "forks_count": self._faker.random_int(min=5, max=1000),
            "open_issues_count": self._faker.random_int(min=0, max=100),
            "pushed_at": datetime.utcnow(),
        }


def populate_database(
    db: Session,
    num_users: int = 50,
    num_projects_to_fetch: int = 5000,  # Augmenté pour 5K projets
    num_actions: int = 1000,  # Plus d'actions pour plus de données
    use_mock_scraper: bool = False,
    repo_file: str = None,
):
    """
    Populates the database with simulated data.

    Args:
        db (Session): The database session.
        num_users (int): The number of users to create.
        num_projects_to_fetch (int): The number of projects to fetch.
        num_actions (int): The number of user actions to simulate.
        use_mock_scraper (bool): If True, use mock data instead of GitHub API.
        repo_file (str): Path to a file containing a list of repositories to scrape.
    """
    log.info("Creating tables if they don't exist...")
    # SAFE: Only creates tables that don't exist, doesn't drop anything
    Base.metadata.create_all(bind=engine)

    log.info("Clearing data only from tables we'll populate...")
    # SAFE: Only clear specific tables we're about to populate, leave others untouched
    # Delete in correct order to respect foreign key constraints
    db.query(Application).delete()
    db.query(Contribution).delete()
    db.query(TeamMember).delete()
    db.query(ProjectRole).delete()
    db.query(Project).delete()
    
    # Clear user-related data that might reference users
    db.query(UserSkill).delete()
    db.query(UserTechnology).delete()
    db.query(CommunityMember).delete()
    
    # Now safe to delete users
    db.query(User).delete()
    db.commit()
    log.info("✅ Cleared only tables we'll populate")

    # --- Create Users ---
    log.info(f"Creating {num_users} users...")
    users = []
    for i in range(num_users):
        user = User(username=f"testuser{i}", email=f"testuser{i}@example.com")
        users.append(user)
    db.add_all(users)
    db.commit()

    # --- Fetch Projects ---
    log.info("Fetching projects...")
    if use_mock_scraper:
        log.info("Using MockGithubScraper for fake project data...")
        scraper = MockGithubScraper()
    else:
        log.info("Using real GithubScraper...")
        scraper = GithubScraper()

    gh_projects = []

    # --- Determine repository source ---
    # Priority: 1. Repo file, 2. Environment variable, 3. Default queries
    if not use_mock_scraper:
        if repo_file and os.path.exists(repo_file):
            log.info(f"Fetching repositories from file: {repo_file}...")
            with open(repo_file, "r") as f:
                repo_names = [line.strip() for line in f if line.strip()]
            gh_projects = scraper.get_repositories_by_names(repo_names)
        else:
            repo_list_str = settings.GITHUB_REPO_LIST
            if repo_list_str:
                log.info("Fetching repositories from GITHUB_REPO_LIST variable...")
                repo_names = [name.strip() for name in repo_list_str.split(",")]
                gh_projects = scraper.get_repositories_by_names(repo_names)

    # If gh_projects is still empty, fall back to fetching using queries
    if not gh_projects:
        log.info("Searching for repositories using queries...")
        # Get queries from environment variables, with defaults
        python_query = os.getenv("GITHUB_PYTHON_QUERY", "language:python stars:>2000")
        js_query = os.getenv("GITHUB_JS_QUERY", "language:javascript stars:>2000")

        # Let's fetch popular Python and JavaScript projects for variety
        gh_projects_py = scraper.get_repositories(
            query=python_query, limit=num_projects_to_fetch // 2
        )
        gh_projects_js = scraper.get_repositories(
            query=js_query, limit=num_projects_to_fetch // 2
        )
        gh_projects = gh_projects_py + gh_projects_js

    if not gh_projects:
        log.warning("Could not fetch any projects from GitHub. Aborting population.")
        return

    # --- Create Projects and Roles ---
    log.info(f"Creating {len(gh_projects)} projects with roles in the database...")
    projects = []
    roles = []
    for gh_project in gh_projects:
        # Get a random user as owner
        owner = random.choice(users) if users else None
        
        project = Project(
            title=gh_project["title"],
            description=gh_project["description"],
            readme=gh_project["readme"],
            language=gh_project["language"],
            topics=",".join(gh_project["topics"]),  # Store topics as a comma-separated string
            github_main_repo=gh_project.get("html_url", None),
            stars_count=gh_project["stargazers_count"],  # <-- Map stargazers_count to stars_count
            forks_count=gh_project["forks_count"],
            open_issues_count=gh_project["open_issues_count"],
            pushed_at=gh_project["pushed_at"],
            owner_id=owner.id if owner else None,
            status="active",
            is_seeking_contributors=True,
            project_type=random.choice(["library", "application", "tool", "framework", "other"]),
            difficulty=random.choice(["easy", "medium", "hard"]),
            license=random.choice(["MIT", "Apache-2.0", "GPL-3.0", "custom", "other"])
        )
        projects.append(project)
    
    # First commit projects to get their IDs
    db.add_all(projects)
    db.commit()
    log.info(f"✅ Created {len(projects)} projects")
    

    
    # Now create roles with valid project IDs
    roles = []
    for project in projects:
        # Create 1-3 fake roles for each project
        for i in range(random.randint(1, 3)):
            role = ProjectRole(
                project_id=project.id,  # Now project.id is valid!
                title=f"Developer Role {i + 1}",
                description=(
                    f"A sample description for role {i + 1} on project {project.title}."
                ),
                responsibility_level=random.choice(["contributor", "maintainer", "lead"]),
                time_commitment=random.choice(["few_hours", "part_time", "full_time"]),
                slots_available=random.randint(1, 3),
                slots_filled=0,
                experience_required=random.choice(["none", "some", "experienced"])
            )
            roles.append(role)
    
    db.add_all(roles)
    db.commit()
    log.info(f"✅ Created {len(roles)} project roles")

    # --- Create "Strong Interest" Actions ---
    log.info(f"Simulating {num_actions} user actions...")
    actions = []
    # Use a cache to prevent creating duplicate relationships in the same run
    team_member_cache = set()
    application_cache = set()

    for _ in range(num_actions):
        user = random.choice(users)
        project = random.choice(projects)
        action_type = random.choice(["member", "contribution", "application"])

        if action_type == "member":
            # Check cache and DB to avoid violating the unique constraint
            if (user.id, project.id) not in team_member_cache and not db.query(
                TeamMember
            ).filter_by(user_id=user.id, project_id=project.id).first():
                # Get a random role for this project
                project_role = db.query(ProjectRole).filter_by(project_id=project.id).first()
                if project_role:
                    actions.append(TeamMember(
                        user_id=user.id,
                        project_id=project.id,
                        project_role_id=project_role.id,
                        status="active",
                        contributions_count=random.randint(0, 5)
                    ))
                    team_member_cache.add((user.id, project.id))

        elif action_type == "contribution":
            actions.append(
                Contribution(
                    user_id=user.id,
                    project_id=project.id,
                    type=random.choice(["code", "design", "documentation", "bug_fix", "feature"]),
                    title=f"Sample contribution on {project.title}",
                    description=f"User contribution to project {project.title}",
                    status=random.choice(["submitted", "reviewed", "merged"])
                )
            )

        elif action_type == "application":
            # Get roles for this project from DB
            project_roles = db.query(ProjectRole).filter_by(project_id=project.id).all()
            if project_roles:
                role = random.choice(project_roles)
                # Check cache and DB to avoid violating the unique constraint
                if (user.id, role.id) not in application_cache and not db.query(
                    Application
                ).filter_by(user_id=user.id, project_role_id=role.id).first():
                    actions.append(Application(
                        user_id=user.id,
                        project_role_id=role.id,
                        portfolio_links='["https://github.com/user", "https://linkedin.com/user"]',
                        availability=random.choice(["immediate", "within_week", "within_month"]),
                        status=random.choice(["pending", "accepted", "rejected"])
                    ))
                    application_cache.add((user.id, role.id))

    db.add_all(actions)
    db.commit()

    # --- Link Projects to Skills, Technologies, and Domains ---
    log.info("Linking projects to skills, technologies, and domains...")
    link_projects_to_entities(db, projects)
    
    # --- Create User Skills and Technologies ---
    log.info("Creating user skills and technologies...")
    create_user_profiles(db, users)
    
    log.info("Database population complete!")
    log.info(f"Total Users: {db.query(User).count()}")
    log.info(f"Total Projects: {db.query(Project).count()}")
    log.info(f"Total Team Memberships: {db.query(TeamMember).count()}")
    log.info(f"Total Contributions: {db.query(Contribution).count()}")
    log.info(f"Total Applications: {db.query(Application).count()}")
    log.info(f"Total Project-Skill links: {db.query(ProjectSkill).count()}")
    log.info(f"Total Project-Technology links: {db.query(ProjectTechnology).count()}")
    log.info(f"Total User-Skill links: {db.query(UserSkill).count()}")
    log.info(f"Total User-Technology links: {db.query(UserTechnology).count()}")


def link_projects_to_entities(db: Session, projects: list[Project]):
    """Link projects to skills, technologies, and domains for coherence."""
    log.info("Linking projects to entities...")
    
    # Get existing entities
    skills = db.query(Skill).all()
    technologies = db.query(Technology).all()
    domains = db.query(DomainCategory).all()
    
    if not skills or not technologies or not domains:
        log.warning("Missing skills, technologies, or domains. Run migrate_schema_v3.py first.")
        return
    
    project_skills = []
    project_technologies = []
    project_domains = []
    
    for project in projects:
        # Link to 2-5 random skills (UNIQUE)
        selected_skills = random.sample(skills, min(random.randint(2, 5), len(skills)))
        project_skills.extend([
            ProjectSkill(
                project_id=project.id,
                skill_id=skill.id,
                is_primary=random.choice([True, False])
            ) for skill in selected_skills
        ])
        
        # Link to 3-8 random technologies (UNIQUE)
        selected_technologies = random.sample(technologies, min(random.randint(3, 8), len(technologies)))
        project_technologies.extend([
            ProjectTechnology(
                project_id=project.id,
                technology_id=tech.id,
                is_primary=random.choice([True, False])
            ) for tech in selected_technologies
        ])
        
        # Link to 1-3 random domains (UNIQUE)
        selected_domains = random.sample(domains, min(random.randint(1, 3), len(domains)))
        project_domains.extend([
            ProjectDomainCategory(
                project_id=project.id,
                domain_category_id=domain.id,
                is_primary=random.choice([True, False])
            ) for domain in selected_domains
        ])
    
    db.add_all(project_skills)
    db.add_all(project_technologies)
    db.add_all(project_domains)
    db.commit()
    
    log.info(f"Linked {len(project_skills)} skills, {len(project_technologies)} technologies, {len(project_domains)} domains to projects")


def create_user_profiles(db: Session, users: list[User]):
    """Create comprehensive user profiles with skills and technologies."""
    log.info("Creating user profiles...")
    
    # Get existing entities
    skills = db.query(Skill).all()
    technologies = db.query(Technology).all()
    
    if not skills or not technologies:
        log.warning("Missing skills or technologies. Run migrate_schema_v3.py first.")
        return
    
    user_skills = []
    user_technologies = []
    
    for user in users:
        # Give each user 3-8 skills with proficiency levels (UNIQUE)
        selected_skills = random.sample(skills, min(random.randint(3, 8), len(skills)))
        user_skills.extend([
            UserSkill(
                user_id=user.id,
                skill_id=skill.id,
                proficiency_level=random.choice(["learning", "basic", "intermediate", "advanced", "expert"]),
                is_primary=random.choice([True, False])
            ) for skill in selected_skills
        ])
        
        # Give each user 4-10 technologies with proficiency levels (UNIQUE)
        selected_technologies = random.sample(technologies, min(random.randint(4, 10), len(technologies)))
        user_technologies.extend([
            UserTechnology(
                user_id=user.id,
                technology_id=tech.id,
                proficiency_level=random.choice(["learning", "basic", "intermediate", "advanced", "expert"]),
                is_primary=random.choice([True, False])
            ) for tech in selected_technologies
        ])
    
    db.add_all(user_skills)
    db.add_all(user_technologies)
    db.commit()
    
    log.info(f"Created {len(user_skills)} user skills and {len(user_technologies)} user technologies")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate the database with test data."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of fetching from GitHub API.",
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
    args = parser.parse_args()

    log.info("Starting database population script...")
    db_session = SessionLocal()
    try:
        # Before running, make sure your .env file is pointing to the TEST database
        # and contains your GITHUB_ACCESS_TOKEN if not using --mock.
        populate_database(
            db_session, 
            num_projects_to_fetch=args.num_projects,
            use_mock_scraper=args.mock, 
            repo_file=args.repo_file
        )
    finally:
        db_session.close()
        log.info("Script finished. Database session closed.")
