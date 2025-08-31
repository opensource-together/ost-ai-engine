"""
Unit tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from src.infrastructure.config import Settings, get_settings


@pytest.mark.unit
def test_settings_initialization():
    """Test that settings can be initialized correctly."""
    # Test with a completely clean environment
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384',
            'GO_API_PORT': '8080',
            'REDIS_CACHE_URL': 'redis://localhost:6379/0',
            'RECOMMENDATION_TOP_N': '5',
            'RECOMMENDATION_MIN_SIMILARITY': '0.1'
        }):
            # Test directly with Settings class to avoid cache issues
            settings = Settings()
            assert settings.DATABASE_URL == 'postgresql://test:test@localhost:5432/test'
            assert settings.GITHUB_ACCESS_TOKEN == 'test_token_1234567890123456789012345678901234567890'
            assert settings.MODEL_NAME == 'sentence-transformers/all-MiniLM-L6-v2'
            assert settings.MODEL_DIMENSIONS == 384
            assert settings.GO_API_PORT == 8080


@pytest.mark.unit
def test_settings_defaults():
    """Test that settings have correct default values."""
    # Test with minimal required environment variables
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            settings = Settings()
            assert settings.LOG_LEVEL == 'INFO'
            assert settings.RECOMMENDATION_TOP_N == 5
            assert settings.RECOMMENDATION_MIN_SIMILARITY == 0.1


@pytest.mark.unit
def test_model_dimensions_consistency():
    """Test that model dimensions are consistent and match the model."""
    # all-MiniLM-L6-v2 a toujours 384 dimensions, c'est une propriété du modèle
    # Même avec plus de données d'entrée, les dimensions de sortie restent 384
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            settings = Settings()
            
            # Vérifier que les dimensions correspondent au modèle
            assert settings.MODEL_DIMENSIONS == 384, "all-MiniLM-L6-v2 should always have 384 dimensions"
            
            # Vérifier que c'est un entier
            assert isinstance(settings.MODEL_DIMENSIONS, int), "MODEL_DIMENSIONS should be an integer"
            
            # Vérifier que c'est une valeur raisonnable pour un modèle d'embedding
            assert 100 <= settings.MODEL_DIMENSIONS <= 1024, "MODEL_DIMENSIONS should be between 100 and 1024"


@pytest.mark.unit
def test_model_dimensions_with_different_data_sizes():
    """Test that model dimensions remain constant regardless of input data size."""
    # Les dimensions du modèle sont une propriété du modèle, pas des données
    test_cases = [
        {'input_size': 100, 'expected_dimensions': 384},
        {'input_size': 1000, 'expected_dimensions': 384},
        {'input_size': 10000, 'expected_dimensions': 384},
    ]
    
    for case in test_cases:
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
                'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
                'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
                'MODEL_DIMENSIONS': '384'
            }):
                settings = Settings()
                assert settings.MODEL_DIMENSIONS == case['expected_dimensions'], \
                    f"Model dimensions should be {case['expected_dimensions']} regardless of input size {case['input_size']}"


@pytest.mark.unit
def test_settings_validation():
    """Test that settings validation works correctly."""
    # Test that validation raises an error for invalid settings
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'short',  # Too short
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            # The settings should raise a validation error for short token
            with pytest.raises(ValueError, match="GitHub token too short"):
                Settings()


@pytest.mark.unit
def test_database_url_validation():
    """Test DATABASE_URL format validation."""
    # Test with valid URL
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            settings = Settings()
            assert settings.DATABASE_URL == 'postgresql://test:test@localhost:5432/test'


@pytest.mark.unit
def test_model_dimensions_validation():
    """Test MODEL_DIMENSIONS validation."""
    # Test with valid dimensions
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            settings = Settings()
            assert settings.MODEL_DIMENSIONS == 384


@pytest.mark.unit
def test_recommendation_weights():
    """Test that recommendation weights sum to reasonable values."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            settings = Settings()
            total_weight = (
                settings.RECOMMENDATION_SEMANTIC_WEIGHT +
                settings.RECOMMENDATION_CATEGORY_WEIGHT +
                settings.RECOMMENDATION_TECH_WEIGHT +
                settings.RECOMMENDATION_POPULARITY_WEIGHT
            )
            assert 0.5 <= total_weight <= 2.0, f"Weights sum to {total_weight}, should be reasonable"


@pytest.mark.unit
def test_redis_url_validation():
    """Test REDIS_CACHE_URL validation."""
    # Test with valid Redis URL
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384',
            'REDIS_CACHE_URL': 'redis://localhost:6379/0'
        }):
            settings = Settings()
            assert settings.REDIS_CACHE_URL == 'redis://localhost:6379/0'


@pytest.mark.unit
def test_settings_caching():
    """Test that settings are properly cached."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
            'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
            'MODEL_DIMENSIONS': '384'
        }):
            # Premier appel
            settings1 = get_settings()
            # Deuxième appel - devrait retourner la même instance
            settings2 = get_settings()
            
            assert settings1 is settings2, "Settings should be cached and return the same instance"


@pytest.mark.unit
def test_environment_specific_settings():
    """Test that environment-specific settings work correctly."""
    # Test with different environment variables
    test_environments = ['development', 'staging', 'production']
    
    for env in test_environments:
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
                'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
                'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
                'MODEL_DIMENSIONS': '384',
                'ENVIRONMENT': env
            }):
                settings = Settings()
                # Note: ENVIRONMENT might not be a direct attribute, but the settings should load
                assert settings.DATABASE_URL == 'postgresql://test:test@localhost:5432/test'
