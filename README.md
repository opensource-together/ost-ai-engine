# OST Data Engine

> **A data processing platform for GitHub repository analysis and intelligent project recommendations**  
> Part of the [OpenSource Together](https://github.com/opensource-together) platform.

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-green.svg)](https://postgresql.org) [![Redis](https://img.shields.io/badge/Redis-6+-red.svg)](https://redis.io) [![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com) [![MLflow](https://img.shields.io/badge/MLflow-Enabled-orange.svg)](https://mlflow.org)

</div>

---

## Quick Start

For detailed setup instructions, see our [Quick Start Guide](docs/deployment/quick-start.md).

### Setup

#### 1. **Environment Setup**
```bash
git clone <repository-url>
cd ost-data-engine
conda create -n data-engine-py13 python=3.13
conda activate data-engine-py13
poetry install
cp .env.example .env
```

#### 2. **Services Launch**
```bash
docker-compose up -d db redis
psql -d OST_PROD -f scripts/database/recreate_schema.sql
python scripts/database/create_test_users.py
```

#### 3. **Pipeline Execution**
```bash
poetry run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select training_data_pipeline
```

#### 4. **Start Go API**
```bash
cd src/api/go
go build -o recommendations-api recommendations.go
./recommendations-api
```

#### 5. **Test API**
```bash
curl "http://localhost:8080/recommendations?user_id={USER_ID}"
```

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

## Configuration

For complete environment configuration details, see [Environment Configuration](docs/deployment/environment.md).

Key settings in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD

# External APIs
GITHUB_ACCESS_TOKEN=your_github_token

# MLflow
MLFLOW_TRACKING_URI=sqlite:///logs/mlflow.db
MLFLOW_ARTIFACT_ROOT=models/mlruns

# API
API_HOST=0.0.0.0
API_PORT=8000
GO_API_PORT=8080
```

---

## Development

```bash
# Tests
poetry run pytest tests/ -v

# Code Quality
poetry run ruff check .
poetry run ruff format .

# MLflow UI
python scripts/start_mlflow_ui.py

# Dagster UI
dagster dev

# Start Go API
cd src/api/go
go build -o recommendations-api recommendations.go
./recommendations-api
```

---

## Documentation

📚 **Complete Documentation**: [docs/](docs/)

### Key Documentation Sections

- **[Quick Start Guide](docs/deployment/quick-start.md)** - Get up and running quickly
- **[Environment Configuration](docs/deployment/environment.md)** - All environment variables explained
- **[REST API Reference](docs/api/rest-api.md)** - Complete API documentation
- **[Go API Implementation](docs/api/go-api.md)** - Go API technical details
- **[ML Pipeline Overview](docs/ml-pipeline/overview.md)** - Machine learning pipeline architecture
- **[Database Schema](docs/database/schema.md)** - Complete database schema documentation

---

<div align="center">

**Made with ❤️ by [@spideystreet](https://github.com/spideystreet) & the OST team**

[![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together)

</div>
