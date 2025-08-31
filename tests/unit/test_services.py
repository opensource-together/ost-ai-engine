"""
Unit tests for application services.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.application.services.recommendation_service import RecommendationService


@pytest.mark.unit
def test_recommendation_service_initialization(mock_settings):
    """Test RecommendationService initialization using centralized mock settings."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings_obj:
        # Configure mock settings with centralized data
        for key, value in mock_settings.items():
            setattr(mock_settings_obj, key, value)
        
        # Mock SQLAlchemy create_engine to avoid real database connection
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            assert service.semantic_weight == mock_settings['RECOMMENDATION_SEMANTIC_WEIGHT']
            assert service.category_weight == mock_settings['RECOMMENDATION_CATEGORY_WEIGHT']
            assert service.tech_weight == mock_settings['RECOMMENDATION_TECH_WEIGHT']
            assert service.popularity_weight == mock_settings['RECOMMENDATION_POPULARITY_WEIGHT']
            assert service.top_n == mock_settings['RECOMMENDATION_TOP_N']
            assert service.min_similarity == mock_settings['RECOMMENDATION_MIN_SIMILARITY']


@pytest.mark.unit
def test_parse_vector_string(sample_vectors):
    """Test vector string parsing using centralized sample vectors."""
    with patch('src.application.services.recommendation_service.settings'):
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Test PostgreSQL format
            result = service.parse_vector_string(sample_vectors['postgresql_format'])
            expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
            np.testing.assert_array_almost_equal(result, expected)
            
            # Test JSON format
            result = service.parse_vector_string(sample_vectors['json_format'])
            np.testing.assert_array_almost_equal(result, expected)
            
            # Test None
            result = service.parse_vector_string(None)
            assert result is None
            
            # Test invalid format
            result = service.parse_vector_string(sample_vectors['invalid_format'])
            assert result is None


@pytest.mark.unit
def test_parse_vector_string_edge_cases():
    """Test edge cases in vector string parsing."""
    with patch('src.application.services.recommendation_service.settings'):
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Test empty string
            result = service.parse_vector_string("")
            assert result is None
            
            # Test empty array
            result = service.parse_vector_string("{}")
            assert result is None
            
            # Test single value
            result = service.parse_vector_string("{0.5}")
            np.testing.assert_array_almost_equal(result, np.array([0.5]))
            
            # Test with spaces
            result = service.parse_vector_string("{ 0.1 , 0.2 , 0.3 }")
            expected = np.array([0.1, 0.2, 0.3])
            np.testing.assert_array_almost_equal(result, expected)


@pytest.mark.unit
def test_get_user_profile_mock(mock_settings, mock_user_profile, mock_db_connection):
    """Test get_user_profile using centralized mocks."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings_obj:
        # Configure mock settings
        for key, value in mock_settings.items():
            setattr(mock_settings_obj, key, value)
        
        # Mock SQLAlchemy create_engine
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Create a proper context manager mock
            context_mock = Mock()
            context_mock.__enter__ = Mock(return_value=mock_db_connection)
            context_mock.__exit__ = Mock(return_value=None)
            mock_engine.connect.return_value = context_mock
            
            result = service.get_user_profile("test_user")
            
            assert result is not None
            assert result["user_id"] == mock_user_profile["user_id"]
            assert result["username"] == mock_user_profile["username"]
            assert result["bio"] == mock_user_profile["bio"]
            assert result["location"] == mock_user_profile["location"]
            assert result["company"] == mock_user_profile["company"]
            np.testing.assert_array_almost_equal(result["embedding"], np.array([0.1, 0.2, 0.3, 0.4, 0.5]))
            assert result["categories"] == mock_user_profile["categories"]
            assert result["tech_stacks"] == mock_user_profile["tech_stacks"]


@pytest.mark.unit
def test_get_user_profile_not_found(mock_settings, mock_db_connection):
    """Test get_user_profile when user is not found using centralized mocks."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings_obj:
        # Configure mock settings
        for key, value in mock_settings.items():
            setattr(mock_settings_obj, key, value)
        
        # Mock SQLAlchemy create_engine
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Override mock to return None (user not found)
            mock_db_connection.execute.return_value.fetchone.return_value = None
            
            # Create a proper context manager mock
            context_mock = Mock()
            context_mock.__enter__ = Mock(return_value=mock_db_connection)
            context_mock.__exit__ = Mock(return_value=None)
            mock_engine.connect.return_value = context_mock
            
            result = service.get_user_profile("nonexistent_user")
            assert result is None


@pytest.mark.unit
def test_get_user_profile_invalid_embedding(mock_settings, mock_db_connection):
    """Test get_user_profile with invalid embedding using centralized mocks."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings_obj:
        # Configure mock settings
        for key, value in mock_settings.items():
            setattr(mock_settings_obj, key, value)
        
        # Mock SQLAlchemy create_engine
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Override mock to return invalid embedding
            mock_user_data_with_invalid_embedding = (
                "123e4567-e89b-12d3-a456-426614174000",  # user_id
                "test_user",                             # username
                "Python developer",                      # bio
                "Paris",                                 # location
                "Tech Corp",                             # company
                "invalid_embedding",                     # embedding_vector (invalid)
                ["Data Science"],                        # categories
                ["Python"]                               # tech_stacks
            )
            mock_db_connection.execute.return_value.fetchone.return_value = mock_user_data_with_invalid_embedding
            
            # Create a proper context manager mock
            context_mock = Mock()
            context_mock.__enter__ = Mock(return_value=mock_db_connection)
            context_mock.__exit__ = Mock(return_value=None)
            mock_engine.connect.return_value = context_mock
            
            result = service.get_user_profile("test_user")
            assert result is None


@pytest.mark.unit
def test_error_handling(sample_vectors):
    """Test error handling in recommendation service using centralized sample vectors."""
    with patch('src.application.services.recommendation_service.settings'):
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Test invalid vector parsing
            result = service.parse_vector_string(sample_vectors['invalid_format'])
            assert result is None
            
            # Test empty vector
            result = service.parse_vector_string("")
            assert result is None
            
            # Test None vector
            result = service.parse_vector_string(None)
            assert result is None


@pytest.mark.unit
def test_vector_parsing_performance(sample_vectors):
    """Test vector parsing performance with different formats."""
    with patch('src.application.services.recommendation_service.settings'):
        with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            service = RecommendationService()
            
            # Test performance with PostgreSQL format
            import time
            start_time = time.time()
            for _ in range(1000):
                service.parse_vector_string(sample_vectors['postgresql_format'])
            postgresql_time = time.time() - start_time
            
            # Test performance with JSON format
            start_time = time.time()
            for _ in range(1000):
                service.parse_vector_string(sample_vectors['json_format'])
            json_time = time.time() - start_time
            
            # Both should be reasonably fast
            assert postgresql_time < 1.0, f"PostgreSQL parsing too slow: {postgresql_time:.3f}s"
            assert json_time < 1.0, f"JSON parsing too slow: {json_time:.3f}s"


@pytest.mark.unit
def test_service_with_different_model_dimensions(mock_settings):
    """Test service behavior with different model dimensions."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings_obj:
        # Test with different model dimensions
        test_dimensions = [128, 256, 384, 512, 768]
        
        for dimensions in test_dimensions:
            # Update mock settings
            mock_settings['MODEL_DIMENSIONS'] = dimensions
            for key, value in mock_settings.items():
                setattr(mock_settings_obj, key, value)
            
            # Mock SQLAlchemy create_engine
            with patch('src.application.services.recommendation_service.create_engine') as mock_create_engine:
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                
                service = RecommendationService()
                
                # Service should initialize correctly regardless of dimensions
                assert service.semantic_weight == mock_settings['RECOMMENDATION_SEMANTIC_WEIGHT']
                assert service.category_weight == mock_settings['RECOMMENDATION_CATEGORY_WEIGHT']
                assert service.tech_weight == mock_settings['RECOMMENDATION_TECH_WEIGHT']
                assert service.popularity_weight == mock_settings['RECOMMENDATION_POPULARITY_WEIGHT']
