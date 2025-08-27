# OST Data Engine

> **A data processing platform for GitHub repository analysis and intelligent project recommendations**  
> Part of the [OpenSource Together](https://github.com/opensource-together) platform.

<div align="center">

```ascii
                             ╔══════════════════════════════════════════════════════════════╗
                                                       OST DATA ENGINE                           
                                                                                           
                                    🔍 Projects  →  🧠 ML Processing  →  🎯 API              
                               📊 Data Pipeline    →  🔄 Embeddings    →  💡 Recommendations 
                             ╚══════════════════════════════════════════════════════════════╝
```

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-green.svg)](https://postgresql.org) [![Redis](https://img.shields.io/badge/Redis-6+-red.svg)](https://redis.io) [![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com) [![MLflow](https://img.shields.io/badge/MLflow-Enabled-orange.svg)](https://mlflow.org)

</div>

---

## Quick Start

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

---

## Architecture

```
src/
├──  api/             # FastAPI recommendation service
├──  domain/          # Business logic and models
├──  application/     # Use cases and services
│   └──  services/    # Recommendation engine
├──  infrastructure/  # External adapters
│   ├──  pipeline/    # Dagster orchestration
│   ├──  services/    # MLflow, Redis, external APIs
│   ├──  postgres/    # Database connections
│   └──  cache/       # Redis caching layer
└──  dbt/            # Data transformation models
```

---

## Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **GitHub Scraping** | [@Golang](https://github.com/golang/go) | Efficient data collection |
| **ML Processing** | [@all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Semantic embeddings |
| **Vector Storage** | PostgreSQL + pgvector | Similarity search |
| **Model Persistence** | [@MLFlow](https://github.com/mlflow/mlflow) | Versioning & artifacts |
| **Recommendation Engine** | Custom Python | User-project scoring |
| **API Layer** | FastAPI | Recommendation endpoints |

---

## Configuration

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

# Start API
python src/api/main.py
```

---

## Tech Stack

<div align="center">

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.13 + Dagster + dbt + FastAPI |
| **Database** | PostgreSQL + pgvector + Redis |
| **ML/AI** | MLflow + all-MiniLM-L6-v2 |
| **Infrastructure** | Go (GitHub scraper) + Docker |

</div>

---

<div align="center">

**Made with ❤️ by [@spideystreet](https://github.com/spideystreet) & the OST team**

[![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together)

</div>
