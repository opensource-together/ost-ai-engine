"""
Unit tests for basic functionality and configuration.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


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


def test_settings_import():
    """Test that settings can be imported correctly."""
    try:
        from src.infrastructure.config import settings
        assert settings is not None
    except ImportError as e:
        pytest.fail(f"Failed to import settings: {e}")


def test_database_url_format():
    """Test that DATABASE_URL has correct format."""
    database_url = os.getenv('DATABASE_URL')
    assert database_url is not None, "DATABASE_URL not set"
    assert database_url.startswith('postgresql://'), "DATABASE_URL should start with postgresql://"


def test_github_token_length():
    """Test that GitHub token has reasonable length."""
    token = os.getenv('GITHUB_ACCESS_TOKEN')
    assert token is not None, "GITHUB_ACCESS_TOKEN not set"
    assert len(token) >= 40, "GitHub token seems too short"


if __name__ == "__main__":
    pytest.main([__file__])
