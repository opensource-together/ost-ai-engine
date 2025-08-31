# Testing Overview

This document provides an overview of the testing strategy and structure for the OST Data Engine project.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_env.py          # Environment and configuration tests
│   ├── test_config.py       # Configuration management tests
│   └── test_services.py     # Application services tests
├── integration/             # Integration tests (require services)
│   ├── test_similarity.py   # Database and API integration tests
│   ├── test_cache.py        # Redis cache integration tests
│   └── test_dbt_models.py   # dbt models integration tests
└── performance/             # Performance tests (require external services)
    └── test_api_performance.py  # API performance tests
```

## Test Categories

### Unit Tests
Fast, isolated tests that don't depend on external services.

**Examples:**
- Configuration validation
- Service initialization
- Vector parsing
- Environment variable checks

**Running:**
```bash
# Unit tests only
conda activate data-engine-py13 && pytest tests/unit/ -v

# With coverage
conda activate data-engine-py13 && pytest tests/unit/ -v --cov=src --cov-report=html
```

### Integration Tests
Tests that verify interactions between components and external services.

**Examples:**
- Database connectivity
- Cache operations
- API responses
- Data consistency

**Running:**
```bash
# Integration tests only
conda activate data-engine-py13 && pytest tests/integration/ -v

# Integration tests without slow tests
conda activate data-engine-py13 && pytest tests/integration/ -v -m "not slow"
```

### Performance Tests
Tests that measure system performance under load.

**Examples:**
- API response times
- Concurrent request handling
- Memory usage under load
- Error handling performance

**Running:**
```bash
# Performance tests only (requires API Go to be running)
conda activate data-engine-py13 && pytest tests/performance/ -v
```

## Running Tests

### Development Workflow
```bash
# Daily development (fast)
conda activate data-engine-py13 && pytest tests/unit/ -v

# Before commits (complete)
conda activate data-engine-py13 && pytest -v

# Quick validation (without slow tests)
conda activate data-engine-py13 && pytest tests/unit/ tests/integration/ -v -m "not slow"

# All tests with coverage
conda activate data-engine-py13 && pytest -v --cov=src --cov-report=html
```

### Test Markers
```bash
# Run specific test categories
conda activate data-engine-py13 && pytest -v -m "unit"
conda activate data-engine-py13 && pytest -v -m "integration"
conda activate data-engine-py13 && pytest -v -m "performance"

# Exclude slow tests
conda activate data-engine-py13 && pytest -v -m "not slow"
```

## Centralized Test Fixtures

All test data and mocks are centralized in `tests/conftest.py`:

```python
@pytest.fixture
def mock_settings():
    """Mock settings for unit tests."""
    return {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'MODEL_DIMENSIONS': 384,
        # ... other settings
    }

@pytest.fixture
def mock_user_profile():
    """Mock user profile for testing."""
    return {
        'user_id': '123e4567-e89b-12d3-a456-426614174000',
        'username': 'test_user',
        'embedding': [0.1, 0.2, 0.3, 0.4, 0.5],
        # ... other data
    }

@pytest.fixture
def sample_vectors():
    """Sample vectors for testing."""
    return {
        'postgresql_format': '{0.1,0.2,0.3,0.4,0.5}',
        'json_format': '[0.1,0.2,0.3,0.4,0.5]',
        'invalid_format': 'invalid_vector_string'
    }
```

## Writing Unit Tests

Example using centralized fixtures:

```python
@pytest.mark.unit
def test_parse_vector_string(sample_vectors):
    """Test vector string parsing using centralized sample vectors."""
    with patch('src.application.services.recommendation_service.settings'):
        with patch('src.application.services.recommendation_service.create_engine'):
            service = RecommendationService()
            
            # Test PostgreSQL format
            result = service.parse_vector_string(sample_vectors['postgresql_format'])
            expected = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
            np.testing.assert_array_almost_equal(result, expected)
```

## Writing Integration Tests

Example using database fixtures:

```python
@pytest.mark.integration
def test_similarity_data_quality(db_connection):
    """Test the quality of similarity data."""
    with db_connection as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM "test_similarities"'))
        total_records = result.scalar()
        assert total_records > 0, "test_similarities table is empty"
```

## dbt Integration Tests

The project includes comprehensive dbt integration tests:

```python
@pytest.mark.integration
@pytest.mark.slow
def test_dbt_models_execution():
    """Test that dbt models can be executed successfully."""
    # Tests dbt model execution and validation
    # Ensures data transformation pipeline works correctly
```

**dbt tests include:**
- Model compilation validation
- Project structure verification
- Configuration testing
- Model execution testing
- Data quality validation

## Model Dimensions Testing

The `MODEL_DIMENSIONS` setting is a **model property**, not a data property:

```python
@pytest.mark.unit
def test_model_dimensions_consistency():
    """Test that model dimensions are consistent and match the model."""
    # all-MiniLM-L6-v2 always has 384 dimensions
    # Even with more input data, output dimensions remain 384
    assert settings.MODEL_DIMENSIONS == 384, "all-MiniLM-L6-v2 should always have 384 dimensions"
```

## Test Data Management

Test data is managed through dbt models in `src/dbt/models/test/`:

```
src/dbt/models/test/         # Test data models (dbt)
├── schema.yml               # Documentation and tests
├── test_users.sql           # Test users data
├── test_projects.sql        # Test projects data
└── test_similarities.sql    # Test similarity data
```

## CI/CD Integration

Tests are automatically run in the CI/CD pipeline with proper service dependencies.

## Related Documentation

- [Pytest Best Practices](pytest-best-practices.md) - Detailed testing guidelines
- [DBT Test Models](dbt-test-models.md) - Test data management