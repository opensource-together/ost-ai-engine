import random
from faker import Faker
from sqlalchemy.orm import Session
from src.infrastructure.postgres.database import SessionLocal
from src.domain.models.schema import User, Project, ProjectRole, TeamMember, Contribution, Application

# Initialize Faker to generate fake data
fake = Faker()

def populate_database(db: Session, num_users: int = 50, num_projects: int = 20, num_actions: int = 100):
    """
    Populates the database with simulated data.
    """
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
    for _ in range(num_users):
        user = User(
            username=fake.user_name(),
            email=fake.email()
        )
        users.append(user)
    db.add_all(users)
    db.commit()

    # --- Create Projects and Roles ---
    print(f"Creating {num_projects} projects with roles...")
    projects = []
    roles = []
    for _ in range(num_projects):
        project = Project(
            title=fake.bs().title(),
            description=fake.paragraph(nb_sentences=5)
        )
        projects.append(project)
        # Create 1-3 roles for each project
        for i in range(random.randint(1, 3)):
            role = ProjectRole(
                project=project,
                title=f"{fake.job()} Role {i+1}",
                description=fake.paragraph(nb_sentences=3)
            )
            roles.append(role)
    db.add_all(projects)
    db.add_all(roles)
    db.commit()

    # --- Create "Strong Interest" Actions ---
    print(f"Simulating {num_actions} user actions...")
    actions = []
    for _ in range(num_actions):
        user = random.choice(users)
        project = random.choice(projects)
        action_type = random.choice(['member', 'contribution', 'application'])

        if action_type == 'member':
            # Use a simple check to avoid violating the unique constraint
            if not db.query(TeamMember).filter_by(user_id=user.id, project_id=project.id).first():
                actions.append(TeamMember(user=user, project=project))

        elif action_type == 'contribution':
            actions.append(Contribution(user=user, project=project, title=fake.sentence()))

        elif action_type == 'application':
            # Ensure the project has roles to apply for
            if project.roles:
                role = random.choice(project.roles)
                # Use a simple check to avoid violating the unique constraint
                if not db.query(Application).filter_by(user_id=user.id, project_role_id=role.id).first():
                    actions.append(Application(user=user, role=role))

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
        # e.g., DATABASE_URL="postgresql://user:password@localhost:5434/test_ost_db"
        populate_database(db_session)
    finally:
        db_session.close()
        print("Script finished. Database session closed.") 