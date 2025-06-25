import os

import pytest

from src.application.use_cases.run_training_pipeline import run_training_pipeline
from src.domain.models.schema import Project
from src.infrastructure.postgres.database import SessionLocal


@pytest.fixture(scope="module", autouse=True)
def check_db_has_data():
    """
    A fixture that automatically runs for this test module.
    It verifies that the database contains data before any tests run.
    """
    db = SessionLocal()
    project_count = db.query(Project).count()
    db.close()
    if project_count == 0:
        pytest.fail(
            "The test database is empty. "
            "Please run 'poetry run python scripts/populate_db.py' before this test."
        )


def test_run_training_pipeline_creates_all_artifacts(tmp_path):
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
    # 1. Check that the model directory was created (it should be, by run_training_pipeline).
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
