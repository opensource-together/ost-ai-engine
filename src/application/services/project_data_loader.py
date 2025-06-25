
from sqlalchemy.orm import Session

from src.domain.models.schema import Project
from src.infrastructure.postgres.database import SessionLocal


class ProjectDataLoadingService:
    """
    A service responsible for loading project data from the database.
    """

    def __init__(self, db_session: Session = SessionLocal()):
        """
        Initializes the service with a database session.

        Args:
            db_session (Session): The SQLAlchemy session to use for database operations.
        """
        self.db_session = db_session

    def get_all_projects(self) -> list[Project]:
        """
        Fetches all project records from the database.

        Returns:
            List[Project]: A list of all Project objects.
        """
        try:
            projects = self.db_session.query(Project).all()
            return projects
        finally:
            self.db_session.close()
