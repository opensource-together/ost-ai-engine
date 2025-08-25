from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.domain.models.schema import ProjectRole, ProjectRoleApplication, TeamMember
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

        # --- Query 3: Projects from Application (via ProjectRole) ---
        application_project_ids = (
            self._db.query(ProjectRole.project_id)
            .join(
                ProjectRoleApplication,
                ProjectRoleApplication.project_role_id == ProjectRole.id,
            )
            .filter(ProjectRoleApplication.user_id == user_id)
            .all()
        )

        # Combine results into a single set of unique project IDs
        # The result from a .all() query is a list of tuples, e.g., [(1,), (2,)]
        # so we extract the first element from each tuple.
        interested_project_ids = {pid[0] for pid in team_project_ids}
        interested_project_ids.update(pid[0] for pid in application_project_ids)

        log.info(
            f"[InterestProfile] User {user_id} - Team: {len(team_project_ids)}, Applications: {len(application_project_ids)}"
        )
        log.info(
            f"[InterestProfile] Raw project IDs: {list(interested_project_ids)[:10]}{'...' if len(interested_project_ids) > 10 else ''}"
        )
        return interested_project_ids

    def get_user_interested_projects(self, user_id: UUID) -> set[UUID]:
        """
        Retrieves a unique set of project IDs for a given user.
        This is the main method used by the recommendation system.
        Now uses embed_PROJECTS instead of training_PROJECT.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            set[UUID]: A set of unique project IDs from embed_PROJECTS.
        """
        # Get project IDs from PROJECT table
        project_ids = self.get_user_interest_profile(user_id)
        log.info(
            f"[InterestProfile] User {user_id} - {len(project_ids)} project IDs from PROJECT"
        )

        # Map to embed_PROJECTS IDs using SQL query
        if not project_ids:
            return set()

        # Convert UUIDs to strings for SQL query
        project_id_list = [str(pid) for pid in project_ids]
        placeholders = ",".join([f"'{pid}'" for pid in project_id_list])

        # Query to get embed_PROJECTS IDs that match PROJECT IDs
        query = f"""
        SELECT ep.project_id
        FROM embed_PROJECTS ep
        WHERE ep.project_id IN ({placeholders})
        """

        result = self._db.execute(text(query))
        embedded_project_ids = {UUID(str(row[0])) for row in result}

        log.info(
            f"[InterestProfile] {len(embedded_project_ids)} mapped to embed_PROJECTS"
        )
        return embedded_project_ids
