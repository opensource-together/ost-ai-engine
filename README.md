# OST Data Engine

A data processing platform for GitHub repository analysis and intelligent project recommendations. Part of the [OpenSource Together](https://github.com/opensource-together) platform.

## Overview

Automates GitHub data collection, AI analysis, and vector storage to power intelligent project recommendations.

## Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL 15+ with pgvector
- Redis 6+
- Docker & Docker Compose

### Setup

1. **Environment**
   ```bash
   git clone <repository-url>
   cd ost-data-engine
   conda create -n data-engine-py13 python=3.13
   conda activate data-engine-py13
   poetry install
   cp .env.example .env
   ```

2. **Services**
   ```bash
   docker-compose up -d db redis
   psql -d OST_PROD -f scripts/database/recreate_schema.sql
   python scripts/database/create_test_users.py
   ```

3. **Run Pipeline**
   ```bash
   export DAGSTER_HOME=$(pwd)/logs/dagster
   poetry run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select training_data_pipeline
   ```

## Architecture

```
src/
├── domain/          # Business logic
├── application/     # Use cases
├── infrastructure/  # External adapters
│   ├── pipeline/    # Dagster orchestration
│   ├── services/    # External integrations
│   └── analysis/    # ML models
└── dbt/            # Data transformation
```

## Key Components

- **GitHub Scraping**: Go-based scraper for efficient data collection
- **ML Processing**: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) embeddings
- **Vector Storage**: PostgreSQL with pgvector for similarity search
- **Model Persistence**: MLflow for versioning and artifacts
- **Recommendation Engine**: User-project similarity scoring

## Configuration

Key settings in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
GITHUB_ACCESS_TOKEN=your_github_token
MLFLOW_TRACKING_URI=sqlite:///logs/mlflow.db
MLFLOW_ARTIFACT_ROOT=logs/mlruns
```

## Development

```bash
# Tests
poetry run pytest tests/ -v

# Code quality
poetry run ruff check .
poetry run ruff format .

# MLflow UI
python scripts/start_mlflow_ui.py
```

## Data Flow

1. GitHub scraping → 2. Data transformation → 3. Embedding generation → 4. Similarity calculation → 5. Model persistence → 6. Recommendation API

## Tech Stack

- **Python 3.13** + **Dagster** + **dbt**
- **PostgreSQL** + **pgvector** + **Redis**
- **MLflow** + **[all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)**
- **Go** (GitHub scraper) + **Docker**
