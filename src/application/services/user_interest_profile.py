from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.models.schema import Application, Contribution, ProjectRole, TeamMember


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

        return interested_project_ids
 