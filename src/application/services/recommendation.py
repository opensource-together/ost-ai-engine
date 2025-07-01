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

        # Create a mapping from project ID to index in the similarity matrix
        project_id_to_index = {project.id: idx for idx, project in enumerate(projects)}
        
        # Find indices of user's interested projects
        interested_indices = []
        for project_id in interested_project_ids:
            if project_id in project_id_to_index:
                interested_indices.append(project_id_to_index[project_id])
        
        if not interested_indices:
            return []
        
        # Calculate aggregated similarity scores
        # For each project, sum its similarity with all interested projects
        aggregated_scores = np.zeros(len(projects))
        for idx in interested_indices:
            aggregated_scores += similarity_matrix[idx]
        
        # Set similarity scores of already interested projects to 0
        # (we don't want to recommend projects they're already interested in)
        for idx in interested_indices:
            aggregated_scores[idx] = 0
        
        # Get top N recommendations
        top_indices = np.argsort(aggregated_scores)[::-1][:top_n]
        
        # Convert indices back to project IDs
        recommended_project_ids = [projects[idx].id for idx in top_indices]
        
        return recommended_project_ids
