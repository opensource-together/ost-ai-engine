import pandas as pd
import pytest
from scipy.sparse import issparse

from src.domain.models.schema import Project
from src.infrastructure.analysis.feature_engineer import FeatureEngineer


@pytest.fixture
def mock_projects():
    """Provides a list of mock Project objects for testing."""
    # These are in-memory objects for the unit test, not saved to the DB.
    project1 = Project(
        id=1,
        title="Project Alpha",
        description="A project about machine learning.",
        readme="Readme for Alpha.",
        topics="ml,ai,python",
        language="Python",
        stargazers_count=100,
        forks_count=10,
        open_issues_count=5,
    )
    project2 = Project(
        id=2,
        title="Project Beta",
        description="A project about web development.",
        readme="Readme for Beta.",
        topics="web,javascript,python",
        language="JavaScript",
        stargazers_count=200,
        forks_count=20,
        open_issues_count=15,
    )
    return [project1, project2]


def test_feature_engineer_initialization():
    """Tests if the FeatureEngineer initializes its components correctly."""
    fe = FeatureEngineer()
    assert fe.tfidf_vectorizer is not None
    assert fe.mlb is not None
    assert fe.scaler is not None
    assert fe.tfidf_vectorizer.max_features == 5000


def test_projects_to_dataframe_conversion(mock_projects):
    """Tests the internal conversion of Project objects to a pandas DataFrame."""
    fe = FeatureEngineer()
    df = fe._projects_to_dataframe(mock_projects)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(mock_projects)
    # Check if essential columns are present
    expected_cols = [
        "title",
        "description",
        "readme",
        "topics",
        "stargazers_count",
        "open_issues_count",
    ]
    for col in expected_cols:
        assert col in df.columns


def test_fit_transform_returns_sparse_matrix(mock_projects):
    """Tests that fit_transform returns a sparse matrix, as expected."""
    fe = FeatureEngineer()
    feature_matrix, _, _, _ = fe.fit_transform(mock_projects)
    assert issparse(feature_matrix)


def test_fit_transform_matrix_shape(mock_projects):
    """Tests that the resulting feature matrix has the correct shape."""
    fe = FeatureEngineer()
    feature_matrix, tfidf_vec, mlb, _ = fe.fit_transform(mock_projects)

    # Expected number of rows is the number of projects
    assert feature_matrix.shape[0] == len(mock_projects)

    # Expected number of columns is the sum of features from all sources
    num_tfidf_features = len(tfidf_vec.get_feature_names_out())
    num_topics_features = len(mlb.classes_)
    num_numerical_features = 2  # stargazers_count, open_issues_count

    expected_cols = num_tfidf_features + num_topics_features + num_numerical_features
    assert feature_matrix.shape[1] == expected_cols

    # Check the MultiLabelBinarizer for topics
    # Unique topics are: 'ml', 'ai', 'python', 'web', 'javascript' -> 5
    assert num_topics_features == 5
    # The classes should be sorted alphabetically
    assert all(mlb.classes_ == sorted(["ai", "javascript", "ml", "python", "web"]))
 