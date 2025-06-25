import os
from datetime import datetime

import pytest

from scripts.populate_db import populate_database
from src.application.use_cases.run_training_pipeline import run_training_pipeline
from src.domain.models.schema import Base
from src.infrastructure.postgres.database import SessionLocal, engine


class MockGithubScraper:
    """A mock scraper that returns fake data without making network calls."""

    def get_repositories(self, query: str, limit: int):
        print(f"MOCK: Pretending to search for '{query}' with limit {limit}.")
        fake_projects = []
        for i in range(limit):
            fake_projects.append(
                {
                    "title": f"Mock Project {i+1}",
                    "description": f"A description for mock project {i+1}.",
                    "readme": f"## Mock Readme {i+1}",
                    "topics": [f"topic{i+1}", "mock"],
                    "language": "Python" if i % 2 == 0 else "JavaScript",
                    "html_url": f"http://github.com/mock/project{i+1}",
                    "stargazers_count": (i + 1) * 100,
                    "forks_count": (i + 1) * 10,
                    "open_issues_count": i + 1,
                    "pushed_at": datetime.utcnow(),
                }
            )
        return fake_projects

    def get_repositories_by_names(self, repo_names: list[str]):
        # This can be simple for the test, as we primarily use the search query method
        return self.get_repositories(query="mock_query", limit=len(repo_names))


@pytest.fixture(scope="module")
def populated_db():
    """
    A fixture that creates all tables, populates them with a small set of
    test data using a MOCK scraper, and then drops them after the tests.
    """
    # --- SETUP ---
    print("\nSetting up the test database with MOCK data...")
    Base.metadata.create_all(bind=engine)

    db_session = SessionLocal()
    mock_scraper = MockGithubScraper()

    # Using smaller numbers and the mock scraper for a fast, reliable test run
    populate_database(
        db=db_session,
        num_users=10,
        num_projects_to_fetch=4,
        num_actions=20,
        scraper=mock_scraper,
    )
    db_session.close()
    print("Test database setup complete.")

    yield

    # --- TEARDOWN ---
    print("\nTearing down the test database...")
    Base.metadata.drop_all(bind=engine)
    print("Test database teardown complete.")


def test_run_training_pipeline_creates_all_artifacts(populated_db, tmp_path):
    """
    Integration test for the full `run_training_pipeline` use case.

    This test runs the entire pipeline against a populated database and asserts
    that all expected model artifacts are created and saved to a temporary directory.

    Args:
        tmp_path: A built-in pytest fixture that provides a temporary directory path.
    """
    # pytest's `tmp_path` provides a unique directory for this test run.
    # It's automatically cleaned up by pytest after the test.
    test_model_dir = str(tmp_path)

    print(f"\nRunning training pipeline. Artifacts will be saved to: {test_model_dir}")
    run_training_pipeline(output_dir=test_model_dir)
    print("Pipeline execution finished. Verifying artifacts...")

    # --- ASSERTIONS ---
    # 1. Check that the model directory was created (it should be,
    #    by run_training_pipeline).
    assert os.path.isdir(
        test_model_dir
    ), f"Model directory '{test_model_dir}' was not created."

    # 2. Check that all expected artifact files exist inside the temp directory.
    expected_artifacts = [
        "projects.pkl",
        "similarity_matrix.pkl",
        "tfidf_vectorizer.pkl",
        "mlb_encoder.pkl",
        "scaler.pkl",
    ]

    for artifact in expected_artifacts:
        file_path = os.path.join(test_model_dir, artifact)
        assert os.path.isfile(
            file_path
        ), f"Expected artifact '{artifact}' was not found in {test_model_dir}."

    print("All artifacts successfully verified in temporary directory.")
