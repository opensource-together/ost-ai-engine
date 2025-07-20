import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler

from src.domain.models.schema import Project


class FeatureEngineer:
    """
    Transforms raw project data into a unified feature matrix for model training.
    """

    def __init__(self):
        """
        Initializes the FeatureEngineer with vectorizers and a scaler.
        """
        self.tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self.mlb = MultiLabelBinarizer()
        self.scaler = StandardScaler()

    def _projects_to_dataframe(self, projects: list[Project]) -> pd.DataFrame:
        """Converts a list of Project SQLAlchemy objects into a pandas DataFrame."""
        return pd.DataFrame([p.__dict__ for p in projects])

    def fit_transform(self, projects: list[Project]):
        """
        Fits the vectorizers and scaler, and transforms the project data into a
        feature matrix.

        Args:
            projects (list[Project]): A list of project data from the database.

        Returns:
            scipy.sparse matrix: The combined feature matrix for all projects.
            The fitted models are stored as instance variables.
        """
        df = self._projects_to_dataframe(projects)

        # --- Text Features (TF-IDF) ---
        # Combine text fields, filling any NaN values with an empty string
        df["text_features"] = (
            df["title"].fillna("")
            + " "
            + df["description"].fillna("")
            + " "
            + df["readme"].fillna("")
        )
        text_matrix = self.tfidf_vectorizer.fit_transform(df["text_features"])

        # --- Categorical Features (One-Hot Encoding for Topics) ---
        # Split the comma-separated topics string into a list of strings
        df["topics_list"] = df["topics"].fillna("").str.split(",")
        topics_matrix = self.mlb.fit_transform(df["topics_list"])

        # --- Numerical Features (Standard Scaling) ---
        numerical_features = df[["stargazers_count", "open_issues_count"]].values
        numerical_matrix = self.scaler.fit_transform(numerical_features)

        # --- Combine Features ---
        # hstack is used to horizontally stack the sparse and dense matrices
        combined_features = hstack([text_matrix, topics_matrix, numerical_matrix])

        # Store fitted models as instance variables (they're already fitted)
        self.topic_encoder = self.mlb  # Alias for backward compatibility
        self.numerical_features = ["stargazers_count", "open_issues_count"]

        return combined_features
