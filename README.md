# OST Data Engine

A data processing platform for GitHub repository analysis and intelligent project recommendations.  
Part of the [OpenSource Together](https://github.com/opensource-together) platform.

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
   poetry run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select training_data_pipeline
   ```

## Architecture

```
src/
├── api/             # FastAPI recommendation service
├── domain/          # Business logic and models
├── application/     # Use cases and services
│   └── services/    # Recommendation engine
├── infrastructure/  # External adapters
│   ├── pipeline/    # Dagster orchestration
│   ├── services/    # MLflow, Redis, external APIs
│   ├── postgres/    # Database connections
│   └── cache/       # Redis caching layer
└── dbt/            # Data transformation models
```

**Data Flow:**
```
GitHub Scraping → Data Transformation → Embedding Generation → 
Similarity Calculation → Model Persistence → Recommendation API
```

## Key Components

- **GitHub Scraping**: [@Golang](https://github.com/golang/go) scraper for efficient data collection
- **ML Processing**: [@all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) embeddings
- **Vector Storage**: PostgreSQL with pgvector for similarity search
- **Model Persistence**: [@MLFlow](https://github.com/mlflow/mlflow) for versioning and artifacts
- **Recommendation Engine**: User-project similarity scoring
- **API Layer**: FastAPI service for recommendation endpoints

## Configuration

Key settings in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
GITHUB_ACCESS_TOKEN=your_github_token
MLFLOW_TRACKING_URI=sqlite:///logs/mlflow.db
MLFLOW_ARTIFACT_ROOT=models/mlruns
API_HOST=0.0.0.0
API_PORT=8000
```

## Development

```bash
# Tests
poetry run pytest tests/ -v

# MLflow UI
python scripts/start_mlflow_ui.py

# Start API
python src/api/main.py
```

## Data Flow

1. GitHub scraping → 2. Data transformation → 3. Embedding generation → 4. Similarity calculation → 5. Model persistence → 6. Recommendation API
