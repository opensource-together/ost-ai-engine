# Testing Overview

This document describes the testing strategy and structure for the OST Data Engine.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── __init__.py
│   └── test_basic.py        # Basic functionality tests
└── integration/             # Integration tests (require services)
    ├── __init__.py
    └── test_similarity.py   # Database and API integration tests

src/dbt/models/test/         # Test data models (dbt)
├── schema.yml              # Documentation and tests
├── test_users.sql          # Test users data
├── test_projects.sql       # Test projects data
└── test_similarities.sql   # Test similarity data
```

## Test Data Management

### dbt Models for Test Data

We use **dbt models** to manage test data instead of hardcoded SQL or Python scripts. This approach provides:

- **Version Control**: Test data is versioned with Git
- **Documentation**: Automatic documentation with dbt
- **Data Quality**: Built-in tests for data validation
- **Consistency**: Same data across all environments
- **Maintainability**: Easy to update and extend

### Test Data Models

1. **`test_users.sql`**: Creates test users with different profiles
2. **`test_projects.sql`**: Creates test projects with various technologies  
3. **`test_similarities.sql`**: Generates realistic similarity scores

### Running Test Data Setup

```bash
# Local development
> cd src/dbt
> poetry run dbt run --select tag:test --target dev

# CI/CD
> cd src/dbt
> poetry run dbt run --select tag:test --target ci

# Using the helper script
> python scripts/test_dbt_models.py
```

## Test Categories

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation
**Characteristics**:
- Fast execution (< 1 second per test)
- No external dependencies
- Mock external services
- Test configuration, imports, and basic functionality

**Examples**:
- Environment variable validation
- Configuration loading
- Project structure verification
- Import statements

### Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions and external services
**Characteristics**:
- Require running services (database, API)
- Slower execution
- Test real data flows
- Verify end-to-end functionality

**Examples**:
- Database connectivity and operations
- API endpoint testing
- Data quality validation
- Similarity calculations

## Running Tests

### Local Development

```bash
# Run all tests
> poetry run pytest tests/ -v

# Run only unit tests (fast)
> poetry run pytest tests/unit/ -v

# Run only integration tests
> poetry run pytest tests/integration/ -v

# Run tests with specific markers
> poetry run pytest tests/ -v -m "unit"
> poetry run pytest tests/ -v -m "integration"
> poetry run pytest tests/ -v -m "api"

# Run tests excluding slow ones
> poetry run pytest tests/ -v -m "not slow"

# Run with coverage
> poetry run pytest tests/ -v --cov=src --cov-report=html

# Setup test data first
> python scripts/test_dbt_models.py
```

### CI/CD Pipeline

The CI pipeline runs tests in stages:

1. **Setup Database**: Create extensions and run dbt test models
2. **Unit Tests**: Fast validation of basic functionality
3. **Integration Tests**: Full system validation with test database
4. **Coverage Report**: Overall test coverage analysis

## Test Data

### Test Database Setup

Integration tests use dbt models to create:

- **3 test users** with different profiles (Python, JavaScript, Go)
- **5 test projects** with various technologies
- **15 similarity records** with realistic scores
- **Consistent data relationships** (e.g., Python dev → Python projects = high similarity)

### Data Quality Tests

dbt automatically runs data quality tests:

- **Uniqueness**: Ensure no duplicate IDs
- **Not null**: Required fields are populated
- **Accepted values**: Fields contain expected values
- **Relationships**: Foreign key constraints are valid
- **Range checks**: Numeric values are within expected ranges

### Data Isolation

- Test data is created fresh for each CI run
- No production data is used in tests
- Database is destroyed after tests complete
- Local development uses separate test database

## Test Markers

Pytest markers help categorize and filter tests:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.api`: API-specific tests
- `@pytest.mark.slow`: Slow-running tests

## Best Practices

### Writing Unit Tests

```python
def test_functionality():
    """Test description."""
    # Arrange
    expected = "expected_value"
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected
```

### Writing Integration Tests

```python
@pytest.mark.integration
def test_database_operation():
    """Test database operation."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM test_similarities"))
        count = result.scalar()
        assert count > 0
```

### Test Dependencies

- **Unit tests**: No external dependencies
- **Integration tests**: Require database and services
- **API tests**: Require running Go API

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` environment variable
   - Ensure PostgreSQL is running
   - Verify database extensions are installed

2. **dbt Models Failed**
   - Check dbt profile configuration
   - Verify database credentials
   - Run `dbt debug` to diagnose issues

3. **Go API Not Responding**
   - Check `GO_API_PORT` environment variable
   - Ensure Go API is running
   - Verify API endpoint is accessible

4. **Test Data Missing**
   - Run `python scripts/test_dbt_models.py` to create test data
   - Check dbt model execution logs
   - Verify database schema matches expectations

### Debug Mode

```bash
# Run tests with detailed output
> poetry run pytest tests/ -v -s --tb=long

# Run specific test with debug
> poetry run pytest tests/integration/test_similarity.py::test_similarity_data_quality -v -s

# Debug dbt models
> cd src/dbt
> poetry run dbt debug --target dev
> poetry run dbt run --select tag:test --target dev --debug
```
