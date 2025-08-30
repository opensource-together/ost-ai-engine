# CI/CD Pipeline Documentation

## Overview

The OST Data Engine uses GitHub Actions for continuous integration and deployment. The pipeline is designed with a modular approach, splitting responsibilities across specialized jobs for better performance and debugging.

## Pipeline Structure

### Job Architecture

```
setup → tests-unit → coverage
   ↓
tests-integration → coverage
```

### Job Dependencies

- **`setup`**: No dependencies (runs first)
- **`tests-unit`**: Depends on `setup`
- **`tests-integration`**: Depends on `setup`
- **`tests-performance`**: Depends on `setup`
- **`coverage`**: Depends on `tests-unit` AND `tests-integration` AND `tests-performance`

## Job Details

### 1. Setup Job

**Purpose**: Initialize environment and prepare test data

**Services**:
- PostgreSQL (pgvector/pgvector:pg15)
- Redis (redis:7-alpine)

**Steps**:
1. **Checkout**: Clone repository
2. **Python Setup**: Install Python 3.13
3. **Poetry**: Install and configure Poetry
4. **Cache**: Load cached virtual environment
5. **Dependencies**: Install Python packages
6. **Database Schema**: Create PostgreSQL extensions
7. **Test Data**: Setup test data using dbt or fallback

**Outputs**:
- Cache hit status for other jobs

### 2. Tests Unit Job

**Purpose**: Run fast, isolated unit tests

**Dependencies**: `setup`

**Services**: None (isolated tests)

**Steps**:
1. **Environment Setup**: Python, Poetry, cache
2. **Dependencies**: Install packages
3. **Unit Tests**: Run `pytest tests/unit/ -v -m "unit"`

**Characteristics**:
- Fast execution (< 30 seconds)
- No external dependencies
- Tests configuration, imports, basic functionality

### 3. Tests Integration Job

**Purpose**: Run comprehensive integration tests

**Dependencies**: `setup`

**Services**:
- PostgreSQL (pgvector/pgvector:pg15)
- Redis (redis:7-alpine)

**Steps**:
1. **Environment Setup**: Python, Poetry, cache
2. **Dependencies**: Install packages
3. **Database Schema**: Create extensions and test data
4. **Integration Tests**: Run `pytest tests/integration/ -v -m "integration"`

**Characteristics**:
- Slower execution (1-2 minutes)
- Requires database and services
- Tests end-to-end functionality

### 4. Coverage Job

**Purpose**: Generate comprehensive coverage report

**Dependencies**: `tests-unit` AND `tests-integration` AND `tests-performance`

**Services**:
- PostgreSQL (pgvector/pgvector:pg15)
- Redis (redis:7-alpine)

**Steps**:
1. **Environment Setup**: Python, Poetry, cache
2. **Dependencies**: Install packages
3. **Database Schema**: Create extensions and test data
4. **Coverage Report**: Run `pytest tests/ -v --cov=src --cov-report=xml --cov-report=html`

**Characteristics**:
- Runs only if all test jobs succeed
- Generates coverage reports
- Tests all code with coverage metrics

### 5. Tests Performance Job

**Purpose**: Test API performance and scalability

**Dependencies**: `setup`

**Services**:
- PostgreSQL (pgvector/pgvector:pg15)
- Redis (redis:7-alpine)

**Steps**:
1. **Environment Setup**: Python, Poetry, cache
2. **Dependencies**: Install packages
3. **Database Schema**: Create extensions and test data
4. **Start Go API**: Build and start Go API in background
5. **Performance Tests**: Run `pytest tests/performance/ -v -m "performance"`
6. **Cleanup**: Stop Go API

**Characteristics**:
- Slow execution (2-5 minutes)
- Requires full system setup
- Tests API under load conditions
- Measures response times and throughput

## Configuration

### Environment Variables

```yaml
env:
  POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
  DATABASE_URL: postgresql://${{ secrets.POSTGRES_USER }}:${{ secrets.POSTGRES_PASSWORD }}@localhost:5436/${{ secrets.POSTGRES_DB }}
  GITHUB_ACCESS_TOKEN: ${{ secrets.ACCESS_TOKEN }}
  MODEL_NAME: ${{ secrets.MODEL_NAME }}
  MODEL_DIMENSIONS: ${{ secrets.MODEL_DIMENSIONS }}
  GO_API_PORT: ${{ secrets.GO_API_PORT }}
  REDIS_CACHE_URL: ${{ secrets.REDIS_CACHE_URL }}
  RECOMMENDATION_TOP_N: ${{ secrets.RECOMMENDATION_TOP_N }}
  RECOMMENDATION_MIN_SIMILARITY: ${{ secrets.RECOMMENDATION_MIN_SIMILARITY }}
  PYTHON_VERSION: '3.13'
```

### Service Configuration

#### PostgreSQL Service
```yaml
postgres:
  image: pgvector/pgvector:pg15
  env:
    POSTGRES_USER: ${{ env.POSTGRES_USER }}
    POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
    POSTGRES_DB: ${{ env.POSTGRES_DB }}
  options: >-
    --health-cmd pg_isready
    --health-interval 10s
    --health-timeout 5s
    --health-retries 5
  ports:
    - 5436:5432
```

#### Redis Service
```yaml
redis:
  image: redis:7-alpine
  options: >-
    --health-cmd "redis-cli ping"
    --health-interval 10s
    --health-timeout 5s
    --health-retries 5
  ports:
    - 6381:6379
```

## Triggers

### Push Events
```yaml
on:
  push:
    branches: [ main, feature/*, release/*, hotfix/*, ci-cd ]
```

### Pull Request Events
```yaml
on:
  pull_request:
    branches: [ main, develop, staging ]
```

## Performance Optimizations

### Caching Strategy
- **Poetry Cache**: Virtual environment caching
- **Key**: `venv-${{ runner.os }}-${{ steps.setup-python.outputs.python-version }}-${{ hashFiles('**/poetry.lock') }}`
- **Path**: `.venv`

### Parallel Execution
- **Unit Tests**: Run independently after setup
- **Integration Tests**: Run independently after setup
- **Coverage**: Runs after both test jobs complete

### Resource Optimization
- **Services**: Only started when needed
- **Database**: Shared across integration and coverage jobs
- **Cache**: Reused across all jobs

## Error Handling

### Fallback Mechanisms
1. **dbt Failure**: Falls back to direct SQL setup
2. **Service Failure**: Health checks ensure services are ready
3. **Test Failure**: Individual job failures don't block others

### Debugging
- **Job Isolation**: Each job can be debugged independently
- **Service Logs**: Available for PostgreSQL and Redis
- **Test Output**: Detailed pytest output for each job

## Monitoring

### Success Criteria
- **Setup**: Services healthy, database ready
- **Unit Tests**: All unit tests pass
- **Integration Tests**: All integration tests pass
- **Coverage**: Coverage report generated

### Failure Points
- **Service Health**: PostgreSQL/Redis not ready
- **Database Setup**: Extensions or test data creation fails
- **Test Execution**: Individual test failures
- **Dependencies**: Poetry or Python setup issues

## Local Testing

### Using Act
```bash
# Test specific job
act -j tests-unit --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock

# Test all jobs
act push --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock
```

### Environment Setup
```bash
# Create secrets file
cp .secrets.example .secrets
# Edit .secrets with your values

# Run local CI
act -j tests-unit --secret-file .secrets
```

## Best Practices

### 1. Job Design
- **Single Responsibility**: Each job has one clear purpose
- **Dependency Management**: Clear dependency chain
- **Resource Efficiency**: Services only when needed

### 2. Error Handling
- **Graceful Degradation**: Fallback mechanisms
- **Clear Error Messages**: Descriptive failure reasons
- **Debugging Support**: Detailed logs and outputs

### 3. Performance
- **Caching**: Reuse expensive operations
- **Parallelization**: Independent jobs run in parallel
- **Resource Optimization**: Minimal service usage

### 4. Maintenance
- **Modular Structure**: Easy to modify individual jobs
- **Clear Documentation**: Each job's purpose documented
- **Version Control**: All changes tracked in Git

## Troubleshooting

### Common Issues

1. **Service Connection Failed**
   - Check service health commands
   - Verify port mappings
   - Check service logs

2. **Database Setup Failed**
   - Verify PostgreSQL extensions
   - Check dbt model syntax
   - Review fallback script

3. **Test Failures**
   - Check individual test output
   - Verify environment variables
   - Review test data setup

4. **Cache Issues**
   - Clear Poetry cache if needed
   - Check cache key configuration
   - Verify file paths

### Debug Commands

```bash
# Check service status
docker ps

# View service logs
docker logs <container_id>

# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Run specific test locally
poetry run pytest tests/unit/test_basic.py -v
```

## Future Enhancements

### Planned Improvements
1. **Performance**: Optimize job execution time
2. **Monitoring**: Add metrics and alerts
3. **Security**: Enhanced secret management
4. **Scalability**: Support for larger test suites

### Potential Additions
1. **Deployment Jobs**: Production deployment automation
2. **Security Scanning**: Vulnerability scanning
3. **Performance Testing**: Load testing integration
4. **Documentation**: Auto-generated API docs
