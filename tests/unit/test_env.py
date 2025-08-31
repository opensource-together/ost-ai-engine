"""
Unit tests for environment configuration and basic functionality.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_environment_variables():
    """Test that all required environment variables are set and valid."""
    # Variables critiques pour le fonctionnement
    critical_vars = {
        'DATABASE_URL': {
            'required': True,
            'format': 'postgresql://',
            'description': 'Database connection URL'
        },
        'GITHUB_ACCESS_TOKEN': {
            'required': True,
            'min_length': 40,
            'description': 'GitHub API access token'
        },
        'MODEL_NAME': {
            'required': True,
            'expected': 'sentence-transformers/all-MiniLM-L6-v2',
            'description': 'ML model name'
        },
        'MODEL_DIMENSIONS': {
            'required': True,
            'expected': '384',
            'description': 'Model embedding dimensions'
        }
    }
    
    # Variables importantes mais optionnelles
    important_vars = {
        'REDIS_CACHE_URL': {
            'required': False,
            'format': 'redis://',
            'description': 'Redis cache URL'
        },
        'GO_API_PORT': {
            'required': False,
            'type': int,
            'description': 'Go API port'
        },
        'RECOMMENDATION_TOP_N': {
            'required': False,
            'type': int,
            'description': 'Number of recommendations'
        }
    }
    
    # Test des variables critiques
    for var_name, config in critical_vars.items():
        value = os.getenv(var_name)
        assert value is not None, f"Critical environment variable {var_name} ({config['description']}) is not set"
        
        if 'expected' in config:
            assert value == config['expected'], f"{var_name} should be '{config['expected']}', got '{value}'"
        
        if 'min_length' in config:
            assert len(value) >= config['min_length'], f"{var_name} seems too short (min {config['min_length']} chars)"
        
        if 'format' in config:
            assert value.startswith(config['format']), f"{var_name} should start with '{config['format']}'"
    
            # Test des variables importantes
        for var_name, config in important_vars.items():
            value = os.getenv(var_name)
            if value is not None and value != "":  # Si définie et non vide, valider
                if 'format' in config:
                    assert value.startswith(config['format']), f"{var_name} should start with '{config['format']}'"
            
            if 'type' in config and config['type'] == int:
                try:
                    int(value)
                except ValueError:
                    pytest.fail(f"{var_name} should be an integer, got '{value}'")


@pytest.mark.unit
def test_model_configuration():
    """Test that model configuration is valid and consistent."""
    model_name = os.getenv('MODEL_NAME')
    model_dimensions = os.getenv('MODEL_DIMENSIONS')
    
    # Vérifications de base
    assert model_name == 'sentence-transformers/all-MiniLM-L6-v2'
    assert model_dimensions == '384'
    
    # Vérification que les dimensions correspondent au modèle
    # all-MiniLM-L6-v2 a toujours 384 dimensions, même avec plus de données
    # C'est une propriété du modèle, pas des données d'entrée
    expected_dimensions = 384
    assert int(model_dimensions) == expected_dimensions, f"Model dimensions should be {expected_dimensions} for {model_name}"


@pytest.mark.unit
def test_project_structure():
    """Test that essential project files and directories exist."""
    essential_files = [
        'pyproject.toml',
        'poetry.lock',
        'src/',
        'docs/',
        '.github/workflows/ci.yml',
        'tests/',
        'README.md'
    ]
    
    for file_path in essential_files:
        assert os.path.exists(file_path), f"Essential file/directory {file_path} not found"


@pytest.mark.unit
def test_settings_import():
    """Test that settings can be imported correctly."""
    try:
        from src.infrastructure.config import settings
        assert settings is not None
        # Test que les paramètres critiques sont accessibles
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'MODEL_NAME')
        assert hasattr(settings, 'MODEL_DIMENSIONS')
    except ImportError as e:
        pytest.fail(f"Failed to import settings: {e}")


@pytest.mark.unit
def test_database_url_format():
    """Test that DATABASE_URL has correct format."""
    database_url = os.getenv('DATABASE_URL')
    assert database_url is not None, "DATABASE_URL not set"
    assert database_url.startswith('postgresql://'), "DATABASE_URL should start with postgresql://"
    
    # Vérification basique du format
    parts = database_url.replace('postgresql://', '').split('@')
    assert len(parts) == 2, "DATABASE_URL should have format: postgresql://user:pass@host:port/db"


@pytest.mark.unit
def test_github_token_length():
    """Test that GitHub token has reasonable length."""
    token = os.getenv('GITHUB_ACCESS_TOKEN')
    assert token is not None, "GITHUB_ACCESS_TOKEN not set"
    assert len(token) >= 40, "GitHub token seems too short (should be at least 40 characters)"


if __name__ == "__main__":
    pytest.main([__file__])
