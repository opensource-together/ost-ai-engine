"""
Basic tests to ensure the CI pipeline works.
"""

import pytest
import os


def test_environment_variables():
    """Test that required environment variables are set."""
    required_vars = [
        'DATABASE_URL',
        'GITHUB_ACCESS_TOKEN',
        'MODEL_NAME',
        'MODEL_DIMENSIONS'
    ]
    
    for var in required_vars:
        assert os.getenv(var) is not None, f"Environment variable {var} is not set"


def test_database_connection():
    """Test basic database connectivity."""
    from sqlalchemy import create_engine, text
    
    database_url = os.getenv('DATABASE_URL')
    assert database_url is not None, "DATABASE_URL not set"
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")


def test_model_configuration():
    """Test that model configuration is valid."""
    model_name = os.getenv('MODEL_NAME')
    model_dimensions = os.getenv('MODEL_DIMENSIONS')
    
    assert model_name == 'sentence-transformers/all-MiniLM-L6-v2'
    assert model_dimensions == '384'


def test_project_structure():
    """Test that essential project files exist."""
    essential_files = [
        'pyproject.toml',
        'poetry.lock',
        'src/',
        'docs/',
        '.github/workflows/ci.yml'
    ]
    
    for file_path in essential_files:
        assert os.path.exists(file_path), f"Essential file/directory {file_path} not found"


if __name__ == "__main__":
    pytest.main([__file__])
