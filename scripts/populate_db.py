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
    num_projects_to_fetch: int = 20,
    num_actions: int = 100,
    use_mock_scraper: bool = False,
):
    """
    Populates the database with simulated data.

    Args:
        db (Session): The database session.
        num_users (int): The number of users to create.
        num_projects_to_fetch (int): The number of projects to fetch.
        num_actions (int): The number of user actions to simulate.
        use_mock_scraper (bool): If True, use mock data instead of GitHub API.
    """
    log.info("Creating tables if they don't exist...")
    # SAFE: Only creates tables that don't exist, doesn't drop anything
    Base.metadata.create_all(bind=engine)

    log.info("Clearing data only from tables we'll populate...")
    # SAFE: Only clear specific tables we're about to populate, leave others untouched
    db.query(Application).delete()
    db.query(Contribution).delete()
    db.query(TeamMember).delete()
    db.query(ProjectRole).delete()
    db.query(Project).delete()
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

    # Only check for GITHUB_REPO_LIST if not using the mock scraper
    if not use_mock_scraper:
        repo_list_str = settings.GITHUB_REPO_LIST
        if repo_list_str:
            log.info("Fetching repositories from GITHUB_REPO_LIST variable...")
            repo_names = [name.strip() for name in repo_list_str.split(",")]
            gh_projects = scraper.get_repositories_by_names(repo_names)

    # If gh_projects is still empty, fetch using queries
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
        project = Project(
            title=gh_project["title"],
            description=gh_project["description"],
            readme=gh_project["readme"],
            language=gh_project["language"],
            topics=",".join(
                gh_project["topics"]
            ),  # Store topics as a comma-separated string
            html_url=gh_project["html_url"],
            stargazers_count=gh_project["stargazers_count"],
            forks_count=gh_project["forks_count"],
            open_issues_count=gh_project["open_issues_count"],
            pushed_at=gh_project["pushed_at"],
        )
        projects.append(project)
        # Create 1-3 fake roles for each project
        for i in range(random.randint(1, 3)):
            role = ProjectRole(
                project=project,
                title=f"Developer Role {i + 1}",
                description=(
                    f"A sample description for role {i + 1} on project {project.title}."
                ),
            )
            roles.append(role)
    db.add_all(projects)
    db.add_all(roles)
    db.commit()

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
                actions.append(TeamMember(user=user, project=project))
                team_member_cache.add((user.id, project.id))

        elif action_type == "contribution":
            actions.append(
                Contribution(
                    user=user,
                    project=project,
                    title=f"Sample contribution on {project.title}",
                )
            )

        elif action_type == "application":
            if project.roles:
                role = random.choice(project.roles)
                # Check cache and DB to avoid violating the unique constraint
                if (user.id, role.id) not in application_cache and not db.query(
                    Application
                ).filter_by(user_id=user.id, project_role_id=role.id).first():
                    actions.append(Application(user=user, role=role))
                    application_cache.add((user.id, role.id))

    db.add_all(actions)
    db.commit()

    log.info("Database population complete!")
    log.info(f"Total Users: {db.query(User).count()}")
    log.info(f"Total Projects: {db.query(Project).count()}")
    log.info(f"Total Team Memberships: {db.query(TeamMember).count()}")
    log.info(f"Total Contributions: {db.query(Contribution).count()}")
    log.info(f"Total Applications: {db.query(Application).count()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate the database with test data."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of fetching from GitHub API.",
    )
    args = parser.parse_args()

    log.info("Starting database population script...")
    db_session = SessionLocal()
    try:
        # Before running, make sure your .env file is pointing to the TEST database
        # and contains your GITHUB_ACCESS_TOKEN if not using --mock.
        populate_database(db_session, use_mock_scraper=args.mock)
    finally:
        db_session.close()
        log.info("Script finished. Database session closed.")
