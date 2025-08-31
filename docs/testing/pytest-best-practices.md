# Pytest Best Practices for OST Data Engine

## Overview

This document outlines the pytest best practices implemented in the OST Data Engine testing suite.

## Test Organization

### File Naming Convention

- **`test_env.py`**: Environment and configuration tests
- **`test_config.py`**: Configuration management tests
- **`test_services.py`**: Application services tests
- **`test_*.py`**: Integration and performance tests

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_env.py         # Environment tests
│   ├── test_config.py      # Configuration tests
│   └── test_services.py    # Service tests
├── integration/             # Integration tests
└── performance/             # Performance tests
```

## Fixtures and Mocks

### Centralized Fixtures in `conftest.py`

All test data and mocks are centralized in `conftest.py` to ensure consistency and maintainability.

#### Mock Settings Fixture

```python
@pytest.fixture
def mock_settings():
    """Mock settings for unit tests."""
    return {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': 384,
        # ... other settings
    }
```

#### Mock Data Fixtures

```python
@pytest.fixture
def mock_user_profile():
    """Mock user profile for testing."""
    return {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'test_user',
        'bio': 'Python developer',
        # ... other user data
    }
```

#### Sample Vectors Fixture

```python
@pytest.fixture
def sample_vectors():
    """Sample vectors for testing."""
    return {
        'user_embedding': [0.1, 0.2, 0.3, 0.4, 0.5] * 76,  # 384 dimensions
        'postgresql_format': '{0.1,0.2,0.3,0.4,0.5}',
        'json_format': '[0.1,0.2,0.3,0.4,0.5]',
        'invalid_format': 'invalid_vector_string'
    }
```

### Using Fixtures in Tests

```python
@pytest.mark.unit
def test_parse_vector_string(sample_vectors):
    """Test vector string parsing using centralized sample vectors."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        # Use centralized sample vectors
        result = service.parse_vector_string(sample_vectors['postgresql_format'])
        expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        np.testing.assert_array_almost_equal(result, expected)
```

## Test Categories and Markers

### Unit Tests

- **Scope**: Individual components in isolation
- **Speed**: Fast execution (< 1 second per test)
- **Dependencies**: No external services
- **Marker**: `@pytest.mark.unit`

```python
@pytest.mark.unit
def test_environment_variables():
    """Test that all required environment variables are set and valid."""
    # Test implementation
```

### Integration Tests

- **Scope**: Component interactions and external services
- **Speed**: Slower execution (requires services)
- **Dependencies**: Database, API, Redis
- **Marker**: `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_redis_connection():
    """Test Redis connection and basic operations."""
    # Test implementation
```

### Performance Tests

- **Scope**: System performance and scalability
- **Speed**: Slow execution (several minutes)
- **Dependencies**: Full system setup
- **Marker**: `@pytest.mark.performance` and `@pytest.mark.slow`

```python
@pytest.mark.performance
@pytest.mark.slow
def test_api_response_time():
    """Test API response time under normal load."""
    # Test implementation
```

## Environment Testing

### Model Dimensions Consistency

The model dimensions are a property of the model, not the input data. Tests verify this:

```python
@pytest.mark.unit
def test_model_dimensions_consistency():
    """Test that model dimensions are consistent and match the model."""
    # all-MiniLM-L6-v2 a toujours 384 dimensions, c'est une propriété du modèle
    # Même avec plus de données d'entrée, les dimensions de sortie restent 384
    assert settings.MODEL_DIMENSIONS == 384, "all-MiniLM-L6-v2 should always have 384 dimensions"
```

### Environment Variable Validation

Comprehensive environment variable testing:

```python
@pytest.mark.unit
def test_environment_variables():
    """Test that all required environment variables are set and valid."""
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
        # ... other variables
    }
    
    for var_name, config in critical_vars.items():
        value = os.getenv(var_name)
        assert value is not None, f"Critical environment variable {var_name} ({config['description']}) is not set"
        
        if 'format' in config:
            assert value.startswith(config['format']), f"{var_name} should start with '{config['format']}'"
```

## Mock Best Practices

### 1. Use Centralized Mocks

Instead of declaring mocks in each test file, use fixtures from `conftest.py`:

```python
# ❌ Bad: Local mock declaration
def test_something():
    mock_settings = Mock()
    mock_settings.DATABASE_URL = 'postgresql://test:test@localhost:5432/test'
    # ... test implementation

# ✅ Good: Use centralized fixture
def test_something(mock_settings):
    # mock_settings is already configured
    # ... test implementation
```

### 2. Mock at the Right Level

Mock external dependencies, not internal logic:

```python
# ✅ Good: Mock external database connection
with patch.object(service.engine, 'connect', return_value=mock_db_connection):
    result = service.get_user_profile("test_user")

# ❌ Bad: Mock internal parsing logic
with patch.object(service, 'parse_vector_string', return_value=mock_vector):
    # This tests nothing useful
```

### 3. Use Descriptive Mock Names

```python
# ✅ Good: Descriptive names
mock_user_profile = {
    'user_id': '123e4567-e89b-12d3-a456-426614174000',
    'username': 'test_user',
    'bio': 'Python developer'
}

# ❌ Bad: Generic names
mock_data = {
    'id': '123',
    'name': 'user',
    'desc': 'dev'
}
```

## Test Data Management

### Consistent Test Data

All test data is defined in fixtures to ensure consistency:

```python
@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'test_user',
        'bio': 'Python developer',
        'location': 'Paris',
        'company': 'Tech Corp',
        'embedding_vector': '{0.1,0.2,0.3,0.4,0.5}',
        'categories': ['Data Science', 'Machine Learning'],
        'tech_stacks': ['Python', 'TensorFlow']
    }
```

### Vector Testing

Special attention to vector parsing and validation:

```python
@pytest.fixture
def sample_vectors():
    """Sample vectors for testing."""
    return {
        'user_embedding': [0.1, 0.2, 0.3, 0.4, 0.5] * 76,  # 384 dimensions
        'project_embedding': [0.2, 0.3, 0.4, 0.5, 0.6] * 76,  # 384 dimensions
        'postgresql_format': '{0.1,0.2,0.3,0.4,0.5}',
        'json_format': '[0.1,0.2,0.3,0.4,0.5]',
        'invalid_format': 'invalid_vector_string'
    }
```

## Running Tests

### Local Development

```bash
# Run all tests
poetry run pytest tests/ -v

# Run only unit tests (fast)
poetry run pytest tests/unit/ -v

# Run tests with specific markers
poetry run pytest tests/ -v -m "unit"
poetry run pytest tests/ -v -m "integration"
poetry run pytest tests/ -v -m "performance"

# Run tests excluding slow ones
poetry run pytest tests/ -v -m "not slow"

# Run with coverage
poetry run pytest tests/ -v --cov=src --cov-report=html
```

### CI/CD Pipeline

Tests are organized by speed and dependencies:

1. **Unit Tests**: Fast validation of basic functionality
2. **Integration Tests**: Full system validation with test database
3. **Performance Tests**: API performance and load testing

## Best Practices Summary

1. **Centralize mocks and fixtures** in `conftest.py`
2. **Use descriptive names** for test data and mocks
3. **Test model dimensions consistency** (they're model properties, not data properties)
4. **Validate environment variables** comprehensively
5. **Use appropriate markers** for test categorization
6. **Mock external dependencies**, not internal logic
7. **Maintain consistent test data** across all tests
8. **Test edge cases** and error conditions
9. **Measure performance** for critical operations
10. **Document test purpose** with clear docstrings

## Common Patterns

### Testing with Environment Variables

```python
@pytest.fixture
def test_environment():
    """Set up test environment variables."""
    test_env = {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'GITHUB_ACCESS_TOKEN': 'test_token_1234567890123456789012345678901234567890',
        'MODEL_NAME': 'sentence-transformers/all-MiniLM-L6-v2',
        'MODEL_DIMENSIONS': '384',
        # ... other variables
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env
```

### Testing Service Initialization

```python
@pytest.mark.unit
def test_service_initialization(mock_settings):
    """Test service initialization using centralized mock settings."""
    with patch('src.application.services.recommendation_service.settings') as mock_settings_obj:
        # Configure mock settings with centralized data
        for key, value in mock_settings.items():
            setattr(mock_settings_obj, key, value)
        
        service = RecommendationService()
        
        # Verify initialization
        assert service.semantic_weight == mock_settings['RECOMMENDATION_SEMANTIC_WEIGHT']
        assert service.category_weight == mock_settings['RECOMMENDATION_CATEGORY_WEIGHT']
```

### Testing Error Conditions

```python
@pytest.mark.unit
def test_error_handling(sample_vectors):
    """Test error handling in recommendation service using centralized sample vectors."""
    with patch('src.application.services.recommendation_service.settings'):
        service = RecommendationService()
        
        # Test invalid vector parsing
        result = service.parse_vector_string(sample_vectors['invalid_format'])
        assert result is None
        
        # Test empty vector
        result = service.parse_vector_string("")
        assert result is None
```
