# OST Data Engine

Part of the [OpenSource Together](https://github.com/opensource-together) platform.
> **A data processing platform for GitHub repository analysis and intelligent project recommendations.**

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org) [![Go](https://img.shields.io/badge/Go-1.24+-cyan.svg)](https://golang.org) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-green.svg)](https://postgresql.org) [![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com) [![MLflow](https://img.shields.io/badge/MLflow-Enabled-orange.svg)](https://mlflow.org)

</div>

---

## Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data extraction & API** | [@Golang](https://github.com/golang/go) | Recommendation endpoints |
| **Data Transformation** | [@dbt](https://github.com/golang/go) | Transformation models |
| **Recommendation Engine** | [@Python](https://github.com/python) | User-project scoring |
| **ML Processing** | [@all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Semantic embeddings |
| **Model Persistence** | [@MLFlow](https://github.com/mlflow/mlflow) | Versioning & artifacts |
| **Vector Storage** | [@Postgres](https://github.com/postgres/postgres) | Similarity search |

---

## Architecture

```
src/
├──  api/             # Go API recommendation service
├──  domain/          # Business logic and models
├──  application/     # Use cases and services
│   └──  services/    # Recommendation engine
├──  infrastructure/  # External adapters
│   ├──  pipeline/    # Dagster orchestration
│   ├──  services/    # MLflow, Redis, external APIs
│   ├──  postgres/    # Database connections
│   └──  cache/       # Redis caching layer
└──  dbt/             # Data transformation models
```

---

## Quick Start

For detailed setup instructions, see our [Quick Start Guide](docs/deployment/quick-start.md).

### Setup

#### 1. **Environment Setup**
```bash
> git clone <repository-url>
> cd ost-data-engine
> conda create -n data-engine-py13 python=3.13
> conda activate data-engine-py13
> poetry install
> cp .env.example .env
```

#### 2. **Services Launch**
```bash
> docker-compose up -d db redis
> psql -d OST_PROD -f scripts/database/recreate_schema.sql
> python scripts/database/create_test_users.py
```

#### 3. **Pipeline Execution**
```bash
> poetry run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select training_data_pipeline
```

#### 4. **Start Go API**
```bash
> cd src/api/go
> go build -o recommendations-api recommendations.go
> ./recommendations-api
```

#### 5. **Test API**
```bash
> curl "http://localhost:8080/recommendations?user_id={USER_ID}"
```

---

## Configuration

For complete environment configuration details, see [Environment Configuration](docs/deployment/environment.md).

Key settings in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD

# Redis Cache
REDIS_CACHE_URL=redis://localhost:6379/0

# External APIs
GITHUB_ACCESS_TOKEN=your_github_token

# MLflow
MLFLOW_TRACKING_URI=sqlite:///logs/mlflow.db
MLFLOW_ARTIFACT_ROOT=models/mlruns

# Go API
GO_API_PORT=8080
```

---

## Development

```bash
# Tests
> poetry run pytest tests/ -v

# Run tests with markers
> poetry run pytest tests/ -v -m "unit"
> poetry run pytest tests/ -v -m "integration"
> poetry run pytest tests/ -v -m "api"

# Run with coverage
> poetry run pytest tests/ -v --cov=src --cov-report=html

# MLflow UI
> python scripts/start_mlflow_ui.py

# Dagster UI
> dagster dev

# Start Go API
> cd src/api/go
> go build -o recommendations-api recommendations.go
> ./recommendations-api
```

---

## Testing

Our testing strategy is organized into three main categories:

### Test Structure
```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_env.py         # Environment and configuration tests
│   ├── test_config.py      # Configuration management tests
│   └── test_services.py    # Application services tests
├── integration/             # Integration tests (require services)
│   ├── test_similarity.py  # Database and API integration
│   ├── test_cache.py       # Redis cache integration
│   └── test_dbt_models.py  # dbt models integration
└── performance/             # Performance tests (require external services)
    └── test_api_performance.py  # API performance tests
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Fast tests that verify individual components in isolation
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions and external services (including dbt models)
- **Performance Tests** (`tests/performance/`): Tests that measure system performance under load

### Running Tests

#### Development Workflow
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

#### Test Categories
```bash
# Unit tests only
conda activate data-engine-py13 && pytest tests/unit/ -v

# Integration tests only
conda activate data-engine-py13 && pytest tests/integration/ -v

# Performance tests only (requires API Go)
conda activate data-engine-py13 && pytest tests/performance/ -v

# Using markers
conda activate data-engine-py13 && pytest -v -m "unit"
conda activate data-engine-py13 && pytest -v -m "integration"
conda activate data-engine-py13 && pytest -v -m "performance"
```

For detailed testing documentation, see [Testing Overview](docs/testing/overview.md).

### Local CI/CD Testing

Test GitHub Actions workflows locally using our unified script:

```bash
# Test all CI jobs
python scripts/tests/ci_local.py all

# Test specific job
python scripts/tests/ci_local.py tests-unit
python scripts/tests/ci_local.py tests-integration
python scripts/tests/ci_local.py tests-performance

# Available jobs: setup, tests-unit, tests-integration, tests-performance, go-lint, coverage
```

**Prerequisites:**
- Install [Act](https://github.com/nektos/act)
- Docker running
- `.env` file configured

For detailed Act testing documentation, see [Local CI Testing](docs/testing/act-local-testing.md).

---

## Documentation

📚 **Complete Documentation**: [docs/](docs/)

### Key Documentation Sections

- **[Quick Start Guide](docs/deployment/quick-start.md)** - Get up and running quickly
- **[Environment Configuration](docs/deployment/environment.md)** - All environment variables explained
- **[Go API Implementation](docs/api/go-api.md)** - Go API technical details
- **[ML Pipeline Overview](docs/ml-pipeline/overview.md)** - Machine learning pipeline architecture
- **[Database Schema](docs/database/schema.md)** - Complete database schema documentation
- **[Tests](docs/testing/overview.md)** - Tests documentation

---

<div align="center">

**Made with ❤️ by [@spideystreet](https://github.com/spideystreet) & the OST team**

[![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together)

</div>
