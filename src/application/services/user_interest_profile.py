from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.models.schema import Application, Contribution, ProjectRole, TeamMember, ProjectTraining
from src.infrastructure.logger import log


class UserInterestProfileService:
    """
    Fetches a user's "interest profile" from the database.
    The profile consists of a unique set of project IDs based on the user's
    contributions, team memberships, and applications.
    """

    def __init__(self, db: Session):
        """
        Initializes the service with a database session.
        Args:
            db (Session): The SQLAlchemy database session.
        """
        self._db = db

    def get_user_interest_profile(self, user_id: UUID) -> set[UUID]:
        """
        Retrieves a unique set of project IDs for a given user.

        Args:
            user_id (UUID): The ID of the user.

                    Returns:
            set[UUID]: A set of unique project IDs.
        """
        # --- Query 1: Projects from TeamMember ---
        team_project_ids = (
            self._db.query(TeamMember.project_id)
            .filter(TeamMember.user_id == user_id)
            .all()
        )

        # --- Query 2: Projects from Contribution ---
        contribution_project_ids = (
            self._db.query(Contribution.project_id)
            .filter(Contribution.user_id == user_id)
            .all()
        )

        # --- Query 3: Projects from Application (via ProjectRole) ---
        application_project_ids = (
            self._db.query(ProjectRole.project_id)
            .join(Application, Application.project_role_id == ProjectRole.id)
            .filter(Application.user_id == user_id)
            .all()
        )

        # Combine results into a single set of unique project IDs
        # The result from a .all() query is a list of tuples, e.g., [(1,), (2,)]
        # so we extract the first element from each tuple.
        interested_project_ids = {pid[0] for pid in team_project_ids}
        interested_project_ids.update(pid[0] for pid in contribution_project_ids)
        interested_project_ids.update(pid[0] for pid in application_project_ids)

        log.info(f"[InterestProfile] User {user_id} - Team: {len(team_project_ids)}, Contributions: {len(contribution_project_ids)}, Applications: {len(application_project_ids)}")
        log.info(f"[InterestProfile] Raw project IDs: {list(interested_project_ids)[:10]}{'...' if len(interested_project_ids) > 10 else ''}")
        return interested_project_ids
    
    def get_user_interest_profile_from_training(self, user_id: UUID) -> set[UUID]:
        """
        Retrieves a unique set of project IDs from PROJECT_training for a given user.
        Maps PROJECT IDs to PROJECT_training IDs by title.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            set[UUID]: A set of unique project IDs from PROJECT_training.
        """
        # Get project IDs from PROJECT table
        project_ids = self.get_user_interest_profile(user_id)
        log.info(f"[InterestProfile] User {user_id} - {len(project_ids)} project IDs from PROJECT")
        # Get all training projects
        training_projects = self._db.query(ProjectTraining).all()
        title_to_training_id = {project.title: project.id for project in training_projects}
        log.info(f"[InterestProfile] {len(training_projects)} projects in PROJECT_training")
        from src.domain.models.schema import Project
        training_project_ids = set()
        missing_titles = set()
        for project_id in project_ids:
            project = self._db.query(Project).filter(Project.id == project_id).first()
            if project and project.title in title_to_training_id:
                training_project_ids.add(title_to_training_id[project.title])
            else:
                missing_titles.add(getattr(project, 'title', None))
        log.info(f"[InterestProfile] {len(training_project_ids)} mapped to PROJECT_training. Missing: {len(missing_titles)}")
        if missing_titles:
            log.warning(f"[InterestProfile] Titles not found in PROJECT_training: {list(missing_titles)[:5]}{'...' if len(missing_titles) > 5 else ''}")
        return training_project_ids
 