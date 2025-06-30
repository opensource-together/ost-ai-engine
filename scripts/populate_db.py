import os
import random

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
from src.infrastructure.postgres.database import SessionLocal, engine
from src.infrastructure.scraping.github_scraper import GithubScraper


def populate_database(
    db: Session,
    num_users: int = 50,
    num_projects_to_fetch: int = 20,
    num_actions: int = 100,
    scraper=None,  # If None, a real GithubScraper is used. Tests are not written for this, they call mock datas.
):
    """
    Populates the database with simulated data.

    Args:
        db (Session): The database session.
        num_users (int): The number of users to create.
        num_projects_to_fetch (int): The number of projects to fetch.
        num_actions (int): The number of user actions to simulate.
        scraper: An optional scraper instance. If None, a real GithubScraper is used.
    """
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Clearing old data...")
    # Clear existing data to ensure a clean slate
    db.query(Application).delete()
    db.query(Contribution).delete()
    db.query(TeamMember).delete()
    db.query(ProjectRole).delete()
    db.query(Project).delete()
    db.query(User).delete()
    db.commit()

    # --- Create Users ---
    print(f"Creating {num_users} users...")
    users = []
    for i in range(num_users):
        user = User(username=f"testuser{i}", email=f"testuser{i}@example.com")
        users.append(user)
    db.add_all(users)
    db.commit()

    # --- Fetch Real Projects from GitHub ---
    print("Fetching projects...")
    if scraper is None:
        print("Using real GithubScraper...")
        scraper = GithubScraper()
    else:
        print("Using provided mock scraper...")

    gh_projects = []

    repo_list_str = os.getenv("GITHUB_REPO_LIST")
    if repo_list_str:
        print("Fetching repositories from GITHUB_REPO_LIST variable...")
        repo_names = [name.strip() for name in repo_list_str.split(",")]
        gh_projects = scraper.get_repositories_by_names(repo_names)
    else:
        print("Searching for repositories using query variables...")
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
        print("Could not fetch any projects from GitHub. Aborting population.")
        return

    # --- Create Projects and Roles ---
    print(f"Creating {len(gh_projects)} projects with roles in the database...")
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
                title=f"Developer Role {i+1}",
                description=(
                    f"A sample description for role {i+1} on project {project.title}."
                ),
            )
            roles.append(role)
    db.add_all(projects)
    db.add_all(roles)
    db.commit()

    # --- Create "Strong Interest" Actions ---
    print(f"Simulating {num_actions} user actions...")
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

    print("\nDatabase population complete!")
    print(f"Total Users: {db.query(User).count()}")
    print(f"Total Projects: {db.query(Project).count()}")
    print(f"Total Team Memberships: {db.query(TeamMember).count()}")
    print(f"Total Contributions: {db.query(Contribution).count()}")
    print(f"Total Applications: {db.query(Application).count()}")


if __name__ == "__main__":
    print("Starting database population script...")
    db_session = SessionLocal()
    try:
        # Before running, make sure your .env file is pointing to the TEST database
        # and contains your GITHUB_ACCESS_TOKEN.
        populate_database(db_session)
    finally:
        db_session.close()
        print("Script finished. Database session closed.")
