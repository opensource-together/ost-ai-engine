# Quick Start Guide

## Prerequisites

- **Python 3.13+**
- **PostgreSQL 15+** with pgvector extension
- **Redis 6+** (optional, for caching)
- **Go 1.21+** (for API)
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/opensource-together/ost-data-engine.git
cd ost-data-engine
```

### 2. Setup Python Environment

```bash
# Create virtual environment
conda create -n data-engine-py13 python=3.13
conda activate data-engine-py13

# Install dependencies
poetry install
```

### 3. Setup Database

```bash
# Start PostgreSQL and Redis with Docker
docker-compose up -d db redis

# Create database schema
psql -d OST_PROD -f scripts/database/recreate_schema.sql

# Create test users
python scripts/database/create_test_users.py
```

### 4. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Required environment variables:**
```env
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
GITHUB_ACCESS_TOKEN=your_github_token_here
MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
MODEL_DIMENSIONS=384
```

## Running the System

### 1. Start ML Pipeline

```bash
# Run complete pipeline
dagster asset materialize --select user_project_similarities

# Or run individual components
dagster asset materialize --select github_scraping
dagster asset materialize --select user_embeddings
dagster asset materialize --select project_hybrid_embeddings
```

### 2. Start Go API

```bash
# Build and run API
cd src/api/go
go build -o recommendations-api recommendations.go
./recommendations-api
```

### 3. Test the System

```bash
# Test API endpoint
curl "http://localhost:8080/recommendations?user_id={USER_ID}"

# Example with real user ID (replace with actual user ID from your database)
curl "http://localhost:8080/recommendations?user_id={USER_ID}"
```

## Verification

### Check Database

```bash
# Connect to database
psql postgresql://user:password@localhost:5434/OST_PROD

# Check tables
\dt

# Check embeddings
SELECT COUNT(*) FROM embed_USERS;
SELECT COUNT(*) FROM embed_PROJECTS;

# Check similarities
SELECT COUNT(*) FROM "USER_PROJECT_SIMILARITY";
```

### Check API

```bash
# Health check (if implemented)
curl http://localhost:8080/health

# Get recommendations
curl "http://localhost:8080/recommendations?user_id={USER_ID}" | jq
```

## Development Tools

### Dagster UI

```bash
# Start Dagster development server
dagster dev

# Access UI at http://localhost:3000
```

### MLflow UI

```bash
# Start MLflow UI
python scripts/start_mlflow_ui.py

# Access UI at http://localhost:5050
```

### Database Management

```bash
# Connect to database
psql postgresql://user:password@localhost:5434/OST_PROD

# View logs
tail -f logs/data_engine.log
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   docker ps | grep postgres
   
   # Check connection
   psql postgresql://user:password@localhost:5434/OST_PROD -c "SELECT 1;"
   ```

2. **Model Download Failed**
   ```bash
   # Check internet connection
   curl -I https://huggingface.co
   
   # Clear model cache
   rm -rf models/sentence-transformers/
   ```

3. **API Not Starting**
   ```bash
   # Check port availability
   lsof -i :8080
   
   # Check environment variables
   echo $DATABASE_URL
   ```

4. **Pipeline Failures**
   ```bash
   # Check Dagster logs
   dagster asset materialize --select failed_asset_name --verbose
   
   # Check database logs
   tail -f logs/dagster/event.log
   ```

### Performance Tuning

1. **Increase Memory**
   ```bash
   # For embedding generation
   export DAGSTER_MEMORY_LIMIT=4G
   ```

2. **Enable Caching**
   ```bash
   # In .env
   CACHE_ENABLED=true
   REDIS_CACHE_URL=redis://localhost:6380/0
   ```

3. **Optimize Database**
   ```sql
   -- Increase work_mem for vector operations
   SET work_mem = '256MB';
   ```

## Next Steps

1. **Customize Configuration**: Modify `.env` for your environment
2. **Add Authentication**: Implement API authentication
3. **Scale Deployment**: Use Docker containers for production
4. **Monitor Performance**: Add Prometheus metrics
5. **Add Tests**: Implement comprehensive test suite

## Support

- **Documentation**: [docs/](docs/)
