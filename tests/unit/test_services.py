"""
Unit tests for application services.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.application.services.recommendation_service import RecommendationService


@pytest.mark.unit
def test_recommendation_service_initialization():
    """Test RecommendationService initialization."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings:
        mock_settings.RECOMMENDATION_SEMANTIC_WEIGHT = 0.25
        mock_settings.RECOMMENDATION_CATEGORY_WEIGHT = 0.45
        mock_settings.RECOMMENDATION_TECH_WEIGHT = 0.5
        mock_settings.RECOMMENDATION_POPULARITY_WEIGHT = 0.1
        mock_settings.RECOMMENDATION_TOP_N = 5
        mock_settings.RECOMMENDATION_MIN_SIMILARITY = 0.1
        mock_settings.RECOMMENDATION_MAX_PROJECTS = 1000
        mock_settings.RECOMMENDATION_POPULARITY_THRESHOLD = 100000
        mock_settings.DATABASE_URL = 'postgresql://test:test@localhost:5432/test'
        
        service = RecommendationService()
        
        assert service.semantic_weight == 0.25
        assert service.category_weight == 0.45
        assert service.tech_weight == 0.5
        assert service.popularity_weight == 0.1
        assert service.top_n == 5
        assert service.min_similarity == 0.1


@pytest.mark.unit
def test_parse_vector_string():
    """Test vector string parsing."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        # Test PostgreSQL format
        vector_str = "{0.1,0.2,0.3}"
        result = service.parse_vector_string(vector_str)
        expected = np.array([0.1, 0.2, 0.3])
        np.testing.assert_array_almost_equal(result, expected)
        
        # Test JSON format
        vector_str = "[0.1,0.2,0.3]"
        result = service.parse_vector_string(vector_str)
        np.testing.assert_array_almost_equal(result, expected)
        
        # Test None
        result = service.parse_vector_string(None)
        assert result is None
        
        # Test invalid format
        result = service.parse_vector_string("invalid")
        assert result is None


@pytest.mark.unit
def test_cosine_similarity_calculation():
    """Test cosine similarity calculation."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        # Test identical vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        similarity = service.calculate_cosine_similarity(vec1, vec2)
        assert similarity == 1.0
        
        # Test orthogonal vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        similarity = service.calculate_cosine_similarity(vec1, vec2)
        assert similarity == 0.0
        
        # Test opposite vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        similarity = service.calculate_cosine_similarity(vec1, vec2)
        assert similarity == -1.0


@pytest.mark.unit
def test_weighted_similarity_calculation():
    """Test weighted similarity calculation."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        similarities = {
            'semantic': 0.8,
            'category': 0.9,
            'tech': 0.7,
            'popularity': 0.6
        }
        
        weighted_score = service.calculate_weighted_similarity(similarities)
        expected = (
            0.8 * service.semantic_weight +
            0.9 * service.category_weight +
            0.7 * service.tech_weight +
            0.6 * service.popularity_weight
        )
        assert abs(weighted_score - expected) < 1e-6


@pytest.mark.unit
def test_recommendation_filtering():
    """Test recommendation filtering logic."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        recommendations = [
            {'project_id': '1', 'similarity_score': 0.9},
            {'project_id': '2', 'similarity_score': 0.5},
            {'project_id': '3', 'similarity_score': 0.2},
            {'project_id': '4', 'similarity_score': 0.8},
            {'project_id': '5', 'similarity_score': 0.1},
            {'project_id': '6', 'similarity_score': 0.7}
        ]
        
        # Test filtering by minimum similarity
        filtered = service.filter_recommendations(recommendations, min_similarity=0.3)
        assert len(filtered) == 4
        assert all(r['similarity_score'] >= 0.3 for r in filtered)
        
        # Test limiting to top N
        limited = service.limit_recommendations(filtered, top_n=2)
        assert len(limited) == 2
        assert limited[0]['similarity_score'] >= limited[1]['similarity_score']


@pytest.mark.unit
def test_error_handling():
    """Test error handling in recommendation service."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        # Test invalid vector parsing
        result = service.parse_vector_string("invalid_vector")
        assert result is None
        
        # Test empty recommendations
        filtered = service.filter_recommendations([], min_similarity=0.5)
        assert filtered == []
        
        # Test None recommendations
        filtered = service.filter_recommendations(None, min_similarity=0.5)
        assert filtered == []
