from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import spmatrix


class SimilarityCalculator:
    """
    Calculates the similarity between items based on their feature matrix.
    """

    def calculate(self, feature_matrix: spmatrix) -> spmatrix:
        """
        Computes the cosine similarity matrix from a feature matrix.

        Args:
            feature_matrix (spmatrix): A sparse matrix where rows are items
                                       and columns are features.

        Returns:
            spmatrix: A square sparse matrix of cosine similarity scores.
        """
        # The resulting matrix will have a shape of (n_projects, n_projects)
        similarity_matrix = cosine_similarity(feature_matrix)
        return similarity_matrix 