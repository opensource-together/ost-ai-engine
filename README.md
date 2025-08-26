# OST Data Engine

A distributed data processing platform for GitHub repository analysis and intelligent project recommendations.   
This project is part of the [OpenSource Together](https://github.com/opensource-together) platform, which connects project creators with developers, designers, and creatives to build the future of open source together.

The system collects GitHub data, processes it through machine learning pipelines, and stores semantic insights in a vector database. Ultimately, this will power an API that provides intelligent project recommendations to users based on their skills, interests, and preferences.

## Overview

This platform automates the process of:
1. **GitHub Data Collection** - Retrieves repository metadata, commits, and file changes from configured GitHub repositories
2. **AI Analysis** - Processes raw GitHub data through machine learning models to extract semantic insights
3. **Vector Storage** - Stores analyzed data in a PostgreSQL vector database for semantic search and similarity queries
4. **Scalable Processing** - Uses distributed task queues to efficiently handle large numbers of repositories
5. **Recommendation API** - Provides intelligent project recommendations to users based on semantic similarity and user preferences

## Architecture

The project follows a clean architecture pattern with clear separation of concerns:

```
src/
├── domain/                     # Core business logic (no external dependencies)
│   └── models/                 # Domain entities and schema
├── application/                # Business use cases and workflows
│   └── services/               # Core business services
├── infrastructure/             # External system adapters
│   ├── postgres/               # Database persistence
│   ├── pipeline/               # Data processing orchestration
│   │   └── dagster/            # Dagster pipeline assets
│   ├── services/               # External service integrations
│   │   └── go/                 # Go-based GitHub scraper
│   └── analysis/               # ML model implementations
├── dbt/                        # Data transformation models
└── api/                        # External interfaces
```

## Key Components

### Data Pipeline (Dagster)
- **GitHub Scraping**: Go-based scraper for efficient GitHub API data collection
- **Data Transformation**: dbt models for data cleaning and enrichment
- **ML Processing**: Embedding generation using sentence-transformers
- **Vector Storage**: PostgreSQL with pgvector extension for similarity search

### Machine Learning
- **Semantic Embeddings**: [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) model for text embeddings
- **Hybrid Embeddings**: Combines semantic and structured features
- **Model Persistence**: MLflow for model versioning and artifact management
- **Recommendation Engine**: User-project similarity scoring and personalized recommendations

### Database Schema
- **Core Entities**: Users, Projects, Categories, Tech Stacks
- **Relationships**: Many-to-many mappings between entities
- **ML Tables**: Embedding vectors and similarity matrices
- **Vector Support**: pgvector for efficient similarity queries

## Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL 15+ with pgvector extension
- Redis 6+
- Docker & Docker Compose

### Installation

1. **Clone and setup environment**
   ```bash
   git clone <repository-url>
   cd ost-data-engine
   conda create -n data-engine-py13 python=3.13
   conda activate data-engine-py13
   poetry install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

3. **Start services**
   ```bash
   docker-compose up -d db redis
   ```

4. **Initialize database**
   ```bash
   psql -d OST_PROD -f scripts/database/recreate_schema.sql
   python scripts/database/create_test_users.py
   ```

5. **Run the data pipeline**
   ```bash
   export DAGSTER_HOME=$(pwd)/logs/dagster
   poetry run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select training_data_pipeline
   ```

## Configuration

Key configuration parameters in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
REDIS_CACHE_URL=redis://localhost:6380/0

# GitHub API
GITHUB_ACCESS_TOKEN=your_github_token

# MLflow
MLFLOW_TRACKING_URI=sqlite:///logs/mlflow.db
MLFLOW_ARTIFACT_ROOT=logs/mlruns

# Recommendation weights
RECOMMENDATION_SEMANTIC_WEIGHT=0.25
RECOMMENDATION_CATEGORY_WEIGHT=0.45
RECOMMENDATION_TECH_WEIGHT=0.5
```

## Development

### Running Tests
```bash
# Unit tests
poetry run pytest tests/unit/infrastructure/ -v

# Integration tests
poetry run pytest tests/integration/ -v
```

### Code Quality
```bash
# Linting
poetry run ruff check .

# Formatting
poetry run ruff format .

# Type checking
poetry run mypy src/
```

### MLflow UI
```bash
python scripts/start_mlflow_ui.py
# Access at http://localhost:5050
```

## Data Flow

1. **GitHub Scraping**: Go scraper collects repository metadata
2. **Data Transformation**: dbt models clean and enrich the data
3. **Entity Mapping**: Projects mapped to categories and tech stacks
4. **Embedding Generation**: Semantic embeddings created for projects and users
5. **Hybrid Features**: Combined semantic and structured embeddings
6. **Similarity Calculation**: User-project similarity matrices computed
7. **Model Persistence**: MLflow stores model artifacts and versions
8. **Recommendation API**: Serves personalized project recommendations to users

## Technologies

- **Python 3.13**: Core application language
- **Dagster**: Data pipeline orchestration
- **dbt**: Data transformation and modeling
- **PostgreSQL + pgvector**: Vector database for similarity search
- **Redis**: Caching and task queue
- **MLflow**: Model versioning and persistence
- **[all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)**: Semantic embedding generation
- **Go**: High-performance GitHub scraping
- **Docker**: Containerized services

## License

[License information to be added]
