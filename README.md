# OST Data Engine

Part of the [OpenSource Together](https://github.com/opensource-together) platform.  
**A data processing platform for GitHub repository analysis and intelligent project recommendations.**

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org) [![Go](https://img.shields.io/badge/Go-1.24+-cyan.svg)](https://golang.org) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-green.svg)](https://postgresql.org) [![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com) [![MLflow](https://img.shields.io/badge/MLflow-Enabled-orange.svg)](https://mlflow.org)

</div>

---

## Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data extraction & API** | [@Golang](https://github.com/golang/go) | Recommendation endpoints |
| **Data Transformation** | [@dbt](https://github.com/dbt-labs/dbt-core) | Transformation models |
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
├──  application/     # Application services
│   └──  services/    # Recommendation engine
├──  infrastructure/  # External adapters
│   ├──  pipeline/    # Dagster orchestration
│   ├──  services/    # MLflow, Redis, external APIs, Go scraper
│   ├──  postgres/    # Database connections
│   ├──  cache/       # Redis caching layer
│   ├──  analysis/    # Model persistence services
│   └──  monitoring/  # Metrics and observability
└──  dbt/             # Data transformation models
```

---

## Quick Start

For detailed setup instructions, see our [Quick Start Guide](docs/deployment/quick-start.md).

### Setup

#### 1. **Environment Setup (uv)**
```bash
git clone https://github.com/opensource-together/ost-data-engine.git
cd ost-data-engine

# Create and sync venv with uv (uses pyproject [project] deps)
uv sync --group dev

# Copy env file
cp .env.example .env
```

#### 2. **Services Launch**
```bash
> docker-compose up -d db redis
> psql -d OST_PROD -f scripts/database/recreate_schema.sql
> python scripts/database/create_test_users.py
```

#### 3. **Pipeline Execution**
```bash
# Run complete pipeline
uv run dagster job execute -j training_data_pipeline

# Or run individual components
uv run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select github_scraping
uv run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select user_embeddings
uv run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select project_hybrid_embeddings
```

#### 4. **Start Go API**
```bash
> cd src/api/go
> go build -o recommendations-api recommendations.go
> ./recommendations-api
```

#### 5. **Test API**
```bash
> curl "http://localhost:${GO_API_PORT}/recommendations?user_id={USER_ID}"
```

Note: The Go API uses strict environment configuration (no defaults). Ensure `DATABASE_URL`, `GO_API_PORT`, `RECOMMENDATION_TOP_N`, `RECOMMENDATION_MIN_SIMILARITY`, `CACHE_ENABLED`, and `CACHE_TTL` are set (e.g., via Docker Compose) before starting the API.

---

## Configuration

For complete environment configuration details, see [Environment Configuration](docs/deployment/environment.md).

Key settings in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/DB_NAME?sslmode=disable
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=DB_NAME
POSTGRES_HOST=localhost
POSTGRES_PORT=5434

# Redis Cache
REDIS_CACHE_URL=redis://localhost:6379/0

# External APIs
GITHUB_ACCESS_TOKEN=your_github_token

# MLflow
MLFLOW_TRACKING_URI=sqlite:///logs/mlflow.db
MLFLOW_ARTIFACT_ROOT=models/mlruns

# Go API (strict env, no defaults)
GO_API_PORT=8080
RECOMMENDATION_TOP_N=5
RECOMMENDATION_MIN_SIMILARITY=0.1
CACHE_ENABLED=true
CACHE_TTL=3600
```

---

## Development

```bash
# Tests
uv run pytest tests/ -v

# Run tests with markers
uv run pytest tests/ -v -m "unit"
uv run pytest tests/ -v -m "integration"
uv run pytest tests/ -v -m "api"

# Run with coverage
uv run pytest tests/ -v --cov=src --cov-report=html

# MLflow UI
uv run python scripts/start_mlflow_ui.py

# Dagster UI
uv run dagster dev

# Start Go API
cd src/api/go
go build -o recommendations-api recommendations.go
./recommendations-api
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
│   └── test_cache.py       # Redis cache integration
└── performance/             # Performance tests (require external services)
    └── test_api_performance.py  # API performance tests
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Fast tests that verify individual components in isolation
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions and external services
- **Performance Tests** (`tests/performance/`): Tests that measure system performance under load

### Running Tests

#### Development Workflow
```bash
# Daily development (fast)
uv run pytest tests/unit/ -v

# Before commits (complete)
uv run pytest -v

# Quick validation (without slow tests)
uv run pytest tests/unit/ tests/integration/ -v -m "not slow"

# All tests with coverage
uv run pytest -v --cov=src --cov-report=html
```

#### Test Categories
```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# Performance tests only (requires API Go)
uv run pytest tests/performance/ -v

# Using markers
uv run pytest -v -m "unit"
uv run pytest -v -m "integration"
uv run pytest -v -m "performance"
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
