import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, LabelEncoder
import numpy as np
from datetime import datetime

from src.domain.models.schema import Project


class FeatureEngineer:
    """
    Transforms raw project data into a unified feature matrix for model training.
    Enhanced version for future AI integration.
    """

    def __init__(self):
        """
        Initializes the FeatureEngineer with vectorizers and scalers.
        """
        # Enhanced TF-IDF with more features
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words="english", 
            max_features=15000,  # Increased for richer vocabulary
            ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
            min_df=2,  # Minimum document frequency
            max_df=0.95  # Maximum document frequency
        )
        self.mlb = MultiLabelBinarizer()
        self.scaler = StandardScaler()
        
        # New encoders for categorical features
        self.language_encoder = LabelEncoder()
        self.difficulty_encoder = LabelEncoder()
        self.project_type_encoder = LabelEncoder()
        self.license_encoder = LabelEncoder()

    def _projects_to_dataframe(self, projects: list[Project]) -> pd.DataFrame:
        """Converts a list of Project SQLAlchemy objects into a pandas DataFrame."""
        return pd.DataFrame([p.__dict__ for p in projects])

    def _calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived features for better ML performance."""
        df = df.copy()
        
        # Convert dates to datetime with error handling
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        df['pushed_at'] = pd.to_datetime(df['pushed_at'], errors='coerce')
        
        # Project age in days
        # Use timezone-aware now() to match database timestamps
        now_tz = pd.Timestamp.now(tz='UTC')
        
        # Handle cases where dates might be None or NaT
        df['project_age_days'] = (now_tz - df['created_at']).dt.days
        df['project_age_days'] = df['project_age_days'].fillna(365).clip(1)  # Default to 1 year if missing
        
        # Last activity in days
        df['last_activity_days'] = (now_tz - df['pushed_at']).dt.days
        df['last_activity_days'] = df['last_activity_days'].fillna(0).clip(0)
        
        # Engagement metrics
        df['engagement_ratio'] = (df['stars_count'] + df['forks_count']) / df['project_age_days']
        df['activity_score'] = df['open_issues_count'] / df['project_age_days'].clip(1)
        
        # Project health indicators
        df['is_active'] = (df['last_activity_days'] <= 90).astype(int)  # Active in last 3 months
        df['is_seeking'] = df['is_seeking_contributors'].astype(int)
        
        return df

    def fit_transform(self, projects: list[Project]):
        """
        Fits the vectorizers and scaler, and transforms the project data into a
        feature matrix. Enhanced version with more features.

        Args:
            projects (list[Project]): A list of project data from the database.

        Returns:
            scipy.sparse matrix: The combined feature matrix for all projects.
            The fitted models are stored as instance variables.
        """
        df = self._projects_to_dataframe(projects)
        df = self._calculate_derived_features(df)

        # --- Enhanced Text Features (TF-IDF) ---
        # Combine all text fields for rich vocabulary
        df["text_features"] = (
            df["title"].fillna("") + " " +
            df["description"].fillna("") + " " +
            df["readme"].fillna("") + " " +
            df["vision"].fillna("") + " " +
            df["language"].fillna("") + " " +
            df["difficulty"].fillna("") + " " +
            df["project_type"].fillna("") + " " +
            df["license"].fillna("") + " " +
            df["topics"].fillna("") + " " +
            df["status"].fillna("") + " " +
            df["is_seeking_contributors"].map({True: "seeking_contributors", False: "not_seeking"}).fillna("")
        )
        text_matrix = self.tfidf_vectorizer.fit_transform(df["text_features"])

        # --- Categorical Features (One-Hot Encoding for Topics) ---
        df["topics_list"] = df["topics"].fillna("").str.split(",")
        topics_matrix = self.mlb.fit_transform(df["topics_list"])

        # --- Enhanced Categorical Features ---
        # Language encoding
        language_encoded = self.language_encoder.fit_transform(df["language"].fillna("unknown"))
        language_matrix = np.eye(len(self.language_encoder.classes_))[language_encoded]
        
        # Difficulty encoding
        difficulty_encoded = self.difficulty_encoder.fit_transform(df["difficulty"].fillna("unknown"))
        difficulty_matrix = np.eye(len(self.difficulty_encoder.classes_))[difficulty_encoded]
        
        # Project type encoding
        project_type_encoded = self.project_type_encoder.fit_transform(df["project_type"].fillna("unknown"))
        project_type_matrix = np.eye(len(self.project_type_encoder.classes_))[project_type_encoded]

        # --- Enhanced Numerical Features ---
        # Only use features that exist in PROJECT_training table
        available_numerical_features = []
        
        # Core features (always available)
        if "stars_count" in df.columns:
            available_numerical_features.append("stars_count")
        if "open_issues_count" in df.columns:
            available_numerical_features.append("open_issues_count")
        if "forks_count" in df.columns:
            available_numerical_features.append("forks_count")
            
        # Derived features (calculated in _calculate_derived_features)
        if "project_age_days" in df.columns:
            available_numerical_features.append("project_age_days")
        if "last_activity_days" in df.columns:
            available_numerical_features.append("last_activity_days")
        if "engagement_ratio" in df.columns:
            available_numerical_features.append("engagement_ratio")
        if "activity_score" in df.columns:
            available_numerical_features.append("activity_score")
        if "is_active" in df.columns:
            available_numerical_features.append("is_active")
        if "is_seeking" in df.columns:
            available_numerical_features.append("is_seeking")
            
        # Fallback to basic features if derived features not available
        if not available_numerical_features:
            available_numerical_features = ["stars_count", "open_issues_count"]
            
        numerical_features = df[available_numerical_features].fillna(0).values
        numerical_matrix = self.scaler.fit_transform(numerical_features)

        # --- Combine All Features ---
        # Convert dense matrices to sparse for hstack
        from scipy.sparse import csr_matrix
        language_sparse = csr_matrix(language_matrix)
        difficulty_sparse = csr_matrix(difficulty_matrix)
        project_type_sparse = csr_matrix(project_type_matrix)
        numerical_sparse = csr_matrix(numerical_matrix)

        combined_features = hstack([
            text_matrix,           # TF-IDF text features
            topics_matrix,         # Topics one-hot encoding
            language_sparse,       # Language encoding
            difficulty_sparse,     # Difficulty encoding
            project_type_sparse,   # Project type encoding
            numerical_sparse       # Numerical features
        ])

        # Store fitted models as instance variables
        self.topic_encoder = self.mlb
        self.numerical_features = available_numerical_features

        return combined_features

    def get_feature_names(self):
        """Get feature names for interpretability."""
        feature_names = []
        
        # TF-IDF features
        tfidf_names = [f"tfidf_{name}" for name in self.tfidf_vectorizer.get_feature_names_out()]
        feature_names.extend(tfidf_names)
        
        # Topics features
        topic_names = [f"topic_{name}" for name in self.mlb.classes_]
        feature_names.extend(topic_names)
        
        # Language features
        language_names = [f"lang_{name}" for name in self.language_encoder.classes_]
        feature_names.extend(language_names)
        
        # Difficulty features
        difficulty_names = [f"diff_{name}" for name in self.difficulty_encoder.classes_]
        feature_names.extend(difficulty_names)
        
        # Project type features
        project_type_names = [f"type_{name}" for name in self.project_type_encoder.classes_]
        feature_names.extend(project_type_names)
        
        # Numerical features
        feature_names.extend(self.numerical_features)
        
        return feature_names
