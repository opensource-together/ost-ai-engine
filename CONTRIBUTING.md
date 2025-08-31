# Contributing to OST Data Engine

Thank you for your interest in contributing to OST Data Engine! This document provides guidelines and information for contributors.

## Quick Start

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch
4. **Make** your changes
5. **Test** your changes
6. **Submit** a pull request

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Development Setup

### Prerequisites

- **Python 3.13+**
- **Go 1.24+**
- **PostgreSQL 15+** with pgvector extension
- **Redis 7+**
- **Docker & Docker Compose**
- **Poetry** (Python package manager)

### Local Development

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/ost-data-engine.git
cd ost-data-engine

# 2. Set up Python environment
conda create -n data-engine-py13 python=3.13
conda activate data-engine-py13
poetry install

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 4. Start services
docker-compose up -d db redis

# 5. Set up database
psql -d OST_PROD -f scripts/database/recreate_schema.sql
python scripts/database/create_test_users.py
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=OST_PROD

# GitHub API (for testing)
GITHUB_ACCESS_TOKEN=your_github_token_here

# Model Configuration
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
MODEL_DIMENSIONS=384
```

## Project Structure

```
ost-data-engine/
├── src/
│   ├── api/go/              # Go API service
│   ├── application/         # Business logic
│   ├── domain/             # Data models
│   ├── infrastructure/     # External services
│   └── dbt/               # Data transformation
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance tests
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── docker-compose.yml     # Local development
```

## Coding Standards

### Python

- **Style**: Follow [PEP 8](https://pep8.org/) with 88 character line length
- **Linting**: Use `ruff` for linting and formatting
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Use Google-style docstrings

```python
def process_data(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Process input data and return a DataFrame.
    
    Args:
        data: List of dictionaries containing raw data
        
    Returns:
        Processed DataFrame with cleaned data
        
    Raises:
        ValueError: If data format is invalid
    """
    # Implementation
```

### Go

- **Formatting**: Use `gofmt` and `goimports`
- **Linting**: Use `golangci-lint`
- **Comments**: Use Go-style comments for exported functions

```go
// ProcessData processes input data and returns processed results
func ProcessData(data []map[string]interface{}) ([]Result, error) {
    // Implementation
}
```

### SQL (dbt)

- **Naming**: Use snake_case for tables and columns
- **Documentation**: Document all models in `schema.yml`
- **Testing**: Add tests for all models

## Testing Guidelines

### Running Tests

```bash
# All tests
poetry run pytest

# Unit tests only
poetry run pytest tests/unit/

# Integration tests
poetry run pytest tests/integration/

# Performance tests
poetry run pytest tests/performance/

# With coverage
poetry run pytest --cov=src --cov-report=html
```

### Test Requirements

- **Unit Tests**: 90%+ coverage required
- **Integration Tests**: All external services must be tested
- **Performance Tests**: API response times must be under 200ms

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_process_data():
    """Test data processing functionality."""
    # Arrange
    input_data = [{"id": 1, "name": "test"}]
    
    # Act
    result = process_data(input_data)
    
    # Assert
    assert len(result) == 1
    assert result[0]["name"] == "test"
```

## Pull Request Process

### Before Submitting

1. **Test locally**: Ensure all tests pass
2. **Update documentation**: Update relevant docs
3. **Check formatting**: Run `ruff format` and `ruff check`
4. **Update CHANGELOG**: Add entry if needed

### PR Guidelines

- **Title**: Use conventional commit format
- **Description**: Explain what and why, not how
- **Tests**: Include tests for new features
- **Documentation**: Update docs for new features

### Conventional Commits

```
feat: add new recommendation algorithm
fix: resolve database connection issue
docs: update API documentation
test: add integration tests for Go API
refactor: improve embedding generation
```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG updated (if needed)
```

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Create release branch**: `release/v1.2.0`
2. **Update version**: Update `pyproject.toml`
3. **Update CHANGELOG**: Add release notes
4. **Create PR**: Merge to main
5. **Tag release**: Create GitHub release
6. **Deploy**: Deploy to production

## Getting Help

### Communication Channels

- **Issues**: [GitHub Issues](https://github.com/opensource-together/ost-data-engine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/opensource-together/ost-data-engine/discussions)
- **Documentation**: [Project Docs](docs/)

### Before Asking for Help

1. **Check documentation**: Read relevant docs
2. **Search issues**: Look for similar problems
3. **Reproduce**: Ensure you can reproduce the issue
4. **Provide context**: Include environment details

### Issue Templates

Use the appropriate issue template:
- **Bug Report**: For bugs and errors
- **Feature Request**: For new features
- **Documentation**: For doc improvements

## Additional Resources

- [Architecture Overview](docs/architecture/overview.md)
- [API Documentation](docs/api/go-api.md)
- [Testing Guide](docs/testing/overview.md)
- [Deployment Guide](docs/deployment/quick-start.md)

## Contribution Areas

We welcome contributions in these areas:

- **Core Features**: Recommendation algorithms, data processing
- **API Development**: Go API improvements, new endpoints
- **Testing**: Test coverage, new test scenarios
- **Documentation**: Guides, examples, API docs
- **DevOps**: CI/CD improvements, deployment
- **Performance**: Optimization, monitoring
- **Security**: Security improvements, audits

## Recognition

Contributors will be recognized in:
- [Contributors list](https://github.com/opensource-together/ost-data-engine/graphs/contributors)
- Release notes
- Project documentation

Thank you for contributing to OST Data Engine! 🚀
