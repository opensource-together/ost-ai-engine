# Testing Strategy & Documentation

## Overview

Our testing strategy follows a **layered approach** with comprehensive unit tests for the infrastructure layer, ensuring production reliability and maintainability.

## Infrastructure Layer Unit Tests (76 tests)

### 1. Database Tests (22 tests)

**Purpose**: Validate database connection, session management, and data access patterns.

#### `test_database.py` (15 tests)
- **Connection Tests**: Verify PostgreSQL engine creation and URL format
- **Session Management**: Test session lifecycle, cleanup, and context managers
- **Configuration**: Validate database settings and URL validation
- **Error Handling**: Test session creation failures and cleanup on exceptions

#### `test_data_loader.py` (7 tests)
- **Session Management**: Ensure database sessions are always closed (critical for production)
- **Data Formatting**: Validate DataFrame structure and ID column conversion for ML pipeline
- **Error Handling**: Test database connection, query execution, and pandas errors

### 2. GitHub Scraper Tests (12 tests)

**Purpose**: Validate GitHub API integration, rate limiting, and data formatting.

#### `test_github_scraper.py` (12 tests)
- **Configuration**: Test GitHub token initialization and API setup
- **Data Formatting**: Validate repository data structure for ML pipeline compatibility
- **Error Handling**: Test rate limiting, API errors, and individual repository failures
- **Search Functionality**: Validate search limits and batch repository fetching

### 3. Configuration Tests (18 tests)

**Purpose**: Validate environment variable loading, URL validation, and production settings.

#### `test_config.py` (18 tests)
- **Environment Loading**: Test default values, environment overrides, and .env file handling
- **URL Validation**: Validate PostgreSQL and Redis URL formats
- **Model Paths**: Test model directory resolution and path consistency
- **Caching**: Validate singleton pattern and instance consistency
- **Production Readiness**: Test required settings, log levels, and security handling

### 4. Model Persistence Service Tests (22 tests)

**Purpose**: Validate ML model artifact saving, loading, and versioning.

#### `test_model_persistence_service.py` (22 tests)
- **Initialization**: Test directory creation and custom model directories
- **Saving**: Test NumPy arrays (.npy), pickle objects (.pkl), and mixed artifact types
- **Loading**: Test artifact loading, empty directories, and file filtering
- **Vectorizer Extraction**: Test TF-IDF vectorizer extraction from feature engineers
- **Versioning**: Test model versioning with `save_model()` and `load_model()`
- **Error Handling**: Test permissions, missing files, and corrupted data

## Test Execution

### Run All Infrastructure Tests
```bash
poetry run pytest tests/unit/infrastructure/ -v
```

### Run Specific Component Tests
```bash
# Database tests
poetry run pytest tests/unit/infrastructure/postgres/ -v

# GitHub scraper tests
poetry run pytest tests/unit/infrastructure/scraping/ -v

# Configuration tests
poetry run pytest tests/unit/infrastructure/test_config.py -v

# Model persistence tests
poetry run pytest tests/unit/infrastructure/analysis/ -v
```

### Test Coverage
```bash
poetry run pytest tests/unit/infrastructure/ --cov=src/infrastructure --cov-report=html
```

## Production Critical Tests

### Session Management (Database)
- **Why Critical**: Database connections must be properly closed to prevent resource leaks
- **Tests**: `test_session_is_always_closed`, `test_session_closed_on_exception`
- **Impact**: Memory leaks, connection pool exhaustion

### Error Handling (All Components)
- **Why Critical**: Graceful failure handling prevents application crashes
- **Tests**: Rate limiting, API errors, file system errors, corrupted data
- **Impact**: Application stability, user experience

### Data Formatting (ML Pipeline)
- **Why Critical**: Incorrect data formats break ML training and inference
- **Tests**: DataFrame structure, ID column types, required fields
- **Impact**: ML pipeline failures, incorrect recommendations

### Configuration Validation
- **Why Critical**: Invalid configuration causes deployment failures
- **Tests**: URL formats, required settings, environment variable loading
- **Impact**: Application startup failures, runtime errors

## Test Isolation & Best Practices

### Temporary Directories
- All file system tests use `tempfile.TemporaryDirectory()`
- Automatic cleanup prevents test pollution
- Isolated test environments

### Mocking Strategy
- External dependencies (GitHub API, database) are mocked
- Environment variables are isolated with `patch.dict()`
- No external service dependencies

### Error Simulation
- Real error conditions are simulated (read-only directories, corrupted files)
- Tests validate actual error handling, not just mocks
- Production-like error scenarios

## Integration with CI/CD

### GitHub Actions Pipeline
- All 76 infrastructure tests run on every commit
- Tests run in isolated environments with PostgreSQL and Redis services
- Failures block deployment to prevent production issues

### Pre-commit Validation
```bash
# Run before committing
poetry run pytest tests/unit/infrastructure/ -v
poetry run ruff check .
poetry run black --check .
```

## Next Steps

### Phase 2: Integration Tests
- End-to-end workflow testing
- API endpoint validation
- Complete ML pipeline testing

### Phase 3: Performance Tests
- Database query performance
- ML model loading times
- API response times

### Phase 4: Security Tests
- Input validation
- Authentication/authorization
- Data sanitization

## Test Maintenance

### Adding New Tests
1. Follow existing naming conventions
2. Use appropriate test isolation techniques
3. Focus on production-critical functionality
4. Include error handling scenarios

### Updating Tests
1. Maintain backward compatibility
2. Update tests when interfaces change
3. Validate test coverage remains high
4. Document breaking changes

---

**Current Status**: ✅ **76/76 infrastructure tests passing**
**Coverage**: Comprehensive unit test coverage for all infrastructure components
**Next Phase**: Integration testing for complete workflows 