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
        settings = get_settings()
        assert settings.DATABASE_URL == 'postgresql://test:test@localhost:5432/test'
        assert settings.GITHUB_ACCESS_TOKEN == 'test_token_1234567890123456789012345678901234567890'
        assert settings.MODEL_NAME == 'sentence-transformers/all-MiniLM-L6-v2'
        assert settings.MODEL_DIMENSIONS == 384
        assert settings.GO_API_PORT == 8080


@pytest.mark.unit
def test_settings_defaults():
    """Test that settings have correct default values."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384'
    }):
        settings = get_settings()
        assert settings.LOG_LEVEL == 'INFO'
        assert settings.ENVIRONMENT == 'development'
        assert settings.RECOMMENDATION_TOP_N == 5
        assert settings.RECOMMENDATION_MIN_SIMILARITY == 0.1


@pytest.mark.unit
def test_settings_validation():
    """Test that settings validation works correctly."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'short',  # Too short
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384'
    }):
        with pytest.raises(ValueError, match="GitHub token too short"):
            get_settings()


@pytest.mark.unit
def test_database_url_validation():
    """Test DATABASE_URL format validation."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'invalid_url',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384'
    }):
        with pytest.raises(ValueError, match="Invalid DATABASE_URL format"):
            get_settings()


@pytest.mark.unit
def test_model_dimensions_validation():
    """Test MODEL_DIMENSIONS validation."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': 'invalid'  # Not a number
    }):
        with pytest.raises(ValueError):
            get_settings()


@pytest.mark.unit
def test_recommendation_weights():
    """Test that recommendation weights sum to reasonable values."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384'
    }):
        settings = get_settings()
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
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384',
        'REDIS_CACHE_URL': 'invalid_redis_url'
    }):
        with pytest.raises(ValueError, match="Invalid REDIS_CACHE_URL format"):
            get_settings()
