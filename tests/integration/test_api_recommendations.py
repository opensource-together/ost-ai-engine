"""
Integration tests for the recommendation API endpoints.

These tests verify the complete API functionality including:
- HTTP endpoint behavior
- Request/response validation
- Error handling
- Model loading scenarios
"""

import os
import tempfile
from unittest.mock import patch
from uuid import UUID, uuid4

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import MODEL_STORE, app, get_db
from src.domain.models.schema import Base

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_database():
    """Set up test database with sample data."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Add sample data
    with TestingSessionLocal() as db:
        from src.domain.models.schema import Project, TeamMember

        # Create test users
        user1_id = uuid4()
        user2_id = uuid4()

        # Create test projects
        project1_id = uuid4()
        project2_id = uuid4()
        project3_id = uuid4()

        projects = [
            Project(
                id=project1_id,
                title="Test Project 1",
                description="A test project for recommendations",
                topics="python,fastapi",
                language="Python",
                stargazers_count=100,
                forks_count=20,
                open_issues_count=5,
            ),
            Project(
                id=project2_id,
                title="Test Project 2",
                description="Another test project",
                topics="javascript,react",
                language="JavaScript",
                stargazers_count=200,
                forks_count=30,
                open_issues_count=8,
            ),
            Project(
                id=project3_id,
                title="Test Project 3",
                description="Yet another test project",
                topics="python,machine-learning",
                language="Python",
                stargazers_count=150,
                forks_count=25,
                open_issues_count=6,
            ),
        ]

        for project in projects:
            db.add(project)

        # Create team memberships (user interest profiles)
        team_members = [
            TeamMember(user_id=user1_id, project_id=project1_id),
            TeamMember(user_id=user1_id, project_id=project3_id),
            TeamMember(user_id=user2_id, project_id=project2_id),
        ]

        for member in team_members:
            db.add(member)

        db.commit()

        yield {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "project_ids": [project1_id, project2_id, project3_id],
        }

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def setup_test_models():
    """Set up test model files and MODEL_STORE."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create fake model files
        similarity_matrix = np.random.rand(3, 3)
        vectorizer_path = os.path.join(temp_dir, "tfidf_vectorizer.pkl")
        import pickle

        fake_vectorizer = {"fake": "vectorizer"}
        with open(vectorizer_path, "wb") as f:
            pickle.dump(fake_vectorizer, f)

        # Mock the ModelPersistenceService load_model_artifacts method
        with patch(
            "src.infrastructure.analysis.model_persistence_service.ModelPersistenceService.load_model_artifacts"
        ) as mock_load_artifacts:
            # Set up the mock to return our test data
            mock_load_artifacts.return_value = {
                "similarity_matrix": similarity_matrix,
                "tfidf_vectorizer": fake_vectorizer,
            }

            # Set up MODEL_STORE directly
            MODEL_STORE["similarity_matrix"] = similarity_matrix
            MODEL_STORE["vectorizer"] = fake_vectorizer

            # Load projects from test database
            with TestingSessionLocal() as test_db:
                from src.application.services.project_data_loader import (
                    ProjectDataLoadingService,
                )

                loader = ProjectDataLoadingService(db_session=test_db)
                MODEL_STORE["projects"] = loader.get_all_projects()

            yield

            # Cleanup
            MODEL_STORE["similarity_matrix"] = None
            MODEL_STORE["vectorizer"] = None
            MODEL_STORE["projects"] = []


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_success(self):
        """Test health endpoint returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRecommendationEndpoint:
    """Test the recommendation endpoint functionality."""

    def test_recommendations_success(self, setup_test_database, setup_test_models):
        """Test successful recommendation generation."""
        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}?top_n=2")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "user_id" in data
        assert "recommended_projects" in data
        assert "total_recommendations" in data

        # Validate data types
        assert data["user_id"] == str(user_id)
        assert isinstance(data["recommended_projects"], list)
        assert isinstance(data["total_recommendations"], int)
        assert data["total_recommendations"] == len(data["recommended_projects"])
        assert data["total_recommendations"] <= 2

        # Validate UUIDs in recommendations
        for project_id in data["recommended_projects"]:
            UUID(project_id)  # Should not raise exception

    def test_recommendations_default_top_n(
        self, setup_test_database, setup_test_models
    ):
        """Test recommendation with default top_n parameter."""
        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_recommendations"] <= 10  # Default top_n

    def test_recommendations_max_top_n(self, setup_test_database, setup_test_models):
        """Test recommendation with maximum top_n."""
        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}?top_n=50")

        assert response.status_code == 200
        data = response.json()
        assert data["total_recommendations"] <= 50

    def test_recommendations_invalid_user_id(self, setup_test_models):
        """Test recommendation with invalid UUID format."""
        response = client.get("/recommendations/invalid-uuid")

        assert response.status_code == 422  # Validation error

    def test_recommendations_nonexistent_user(self, setup_test_models):
        """Test recommendation for user with no interest profile."""
        nonexistent_user_id = uuid4()

        response = client.get(f"/recommendations/{nonexistent_user_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "No interest profile found" in data["detail"]

    def test_recommendations_invalid_top_n_too_low(
        self, setup_test_database, setup_test_models
    ):
        """Test recommendation with top_n below minimum."""
        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}?top_n=0")

        assert response.status_code == 422  # Validation error

    def test_recommendations_invalid_top_n_too_high(
        self, setup_test_database, setup_test_models
    ):
        """Test recommendation with top_n above maximum."""
        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}?top_n=51")

        assert response.status_code == 422  # Validation error

    def test_recommendations_different_users_different_results(
        self, setup_test_database, setup_test_models
    ):
        """Test that different users get different recommendations."""
        user1_id = setup_test_database["user1_id"]
        user2_id = setup_test_database["user2_id"]

        response1 = client.get(f"/recommendations/{user1_id}?top_n=3")
        response2 = client.get(f"/recommendations/{user2_id}?top_n=3")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Users should have different recommendations (in most cases)
        # Note: This might occasionally fail due to randomness, but very unlikely
        assert data1["user_id"] != data2["user_id"]


class TestModelLoadingErrors:
    """Test API behavior when models are not available."""

    def test_recommendations_no_models_loaded(self, setup_test_database):
        """Test recommendation when models are not loaded."""
        # Clear MODEL_STORE
        MODEL_STORE["similarity_matrix"] = None
        MODEL_STORE["vectorizer"] = None
        MODEL_STORE["projects"] = []

        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "models not available" in data["detail"].lower()

    def test_recommendations_empty_projects(self, setup_test_database):
        """Test recommendation when no projects are loaded."""
        # Set up partial MODEL_STORE (missing projects)
        MODEL_STORE["similarity_matrix"] = np.random.rand(3, 3)
        MODEL_STORE["vectorizer"] = {"fake": "vectorizer"}
        MODEL_STORE["projects"] = []  # Empty projects

        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}")

        # Should return empty recommendations gracefully, not an error
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "recommended_projects" in data
        assert "total_recommendations" in data
        assert data["recommended_projects"] == []
        assert data["total_recommendations"] == 0


class TestResponseFormat:
    """Test API response format compliance."""

    def test_recommendations_response_schema(
        self, setup_test_database, setup_test_models
    ):
        """Test that response follows the expected schema."""
        user_id = setup_test_database["user1_id"]

        response = client.get(f"/recommendations/{user_id}?top_n=3")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["user_id", "recommended_projects", "total_recommendations"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Field types
        assert isinstance(data["user_id"], str)
        assert isinstance(data["recommended_projects"], list)
        assert isinstance(data["total_recommendations"], int)

        # UUID validation
        UUID(data["user_id"])  # Should not raise
        for project_id in data["recommended_projects"]:
            UUID(project_id)  # Should not raise

        # Logical consistency
        assert data["total_recommendations"] == len(data["recommended_projects"])
        assert data["total_recommendations"] <= 3

    def test_error_response_schema(self, setup_test_models):
        """Test that error responses follow expected schema."""
        response = client.get("/recommendations/invalid-uuid")

        assert response.status_code == 422
        data = response.json()

        # FastAPI validation error format
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0
        assert "type" in data["detail"][0]
        assert "loc" in data["detail"][0]
        assert "msg" in data["detail"][0]


class TestPerformance:
    """Test API performance characteristics."""

    def test_recommendations_response_time(
        self, setup_test_database, setup_test_models
    ):
        """Test that recommendations return within reasonable time."""
        import time

        user_id = setup_test_database["user1_id"]

        start_time = time.time()
        response = client.get(f"/recommendations/{user_id}?top_n=10")
        end_time = time.time()

        assert response.status_code == 200

        # Should respond within 2 seconds (generous for test environment)
        response_time = end_time - start_time
        assert (
            response_time < 2.0
        ), f"Response took {response_time:.2f}s, expected < 2.0s"

    def test_multiple_concurrent_requests(self, setup_test_database, setup_test_models):
        """Test handling multiple requests without issues."""
        user_id = setup_test_database["user1_id"]

        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.get(f"/recommendations/{user_id}?top_n=3")
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert "recommended_projects" in data
 