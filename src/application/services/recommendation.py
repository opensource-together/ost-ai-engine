from uuid import UUID

import numpy as np

from src.domain.models.schema import Project


class RecommendationService:
    """
    Generates project recommendations based on user interests and a similarity matrix.
    """

    def get_recommendations(
        self,
        interested_project_ids: set[UUID],
        projects: list[Project],
        similarity_matrix: np.ndarray,
        top_n: int = 10,
    ) -> list[UUID]:
        """
        Calculates project recommendations for a user.

        Args:
            interested_project_ids (set[UUID]): A set of project IDs the user
                has interacted with.
            projects (List[Project]): The full list of projects, in the same
                order as the matrix.
            similarity_matrix (np.ndarray): The pre-computed project-project
                similarity matrix.
            top_n (int): The number of recommendations to return.

        Returns:
            List[UUID]: A list of recommended project IDs.
        """
        if not interested_project_ids:
            return []

        # ... existing code ...
