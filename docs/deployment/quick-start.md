# Quick Start Guide

## Prerequisites

- **Python 3.13+**
- **PostgreSQL 15+** with pgvector extension
- **Redis 7+**
- **Go 1.24+**
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/opensource-together/ost-ai-engine.git
cd ost-ai-engine
```

### 2. Setup Python Environment

```bash
# Create virtual environment
conda create -n data-engine-py13 python=3.13
conda activate data-engine-py13

# Install dependencies
poetry install
```

### 3. Setup Database and Cache

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
REDIS_CACHE_URL=redis://localhost:6379/0
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
# Option 1: Build and run locally
cd src/api/go
go build -o recommendations-api recommendations.go
./recommendations-api

# Option 2: Run with Docker Compose
docker-compose up go-api
```

### 3. Test the System

```bash
# Test API endpoint
curl "http://localhost:8080/recommendations?user_id={USER_ID}"

# Example with real user ID (replace with actual user ID from your database)
curl "http://localhost:8080/recommendations?user_id={USER_ID}"
```

## Testing with Act (Local CI/CD)

### Setup Act for Local Testing

```bash
# Install Act
brew install act

# Create secrets file for testing
cp .secrets.example .secrets
# Edit .secrets with your test values
```

### Run Local CI Tests

```bash
# macOS (recommended command)
act -j test --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock

# Alternative commands
act --list  # List available jobs
act -j test --secret-file .secrets --pull=false  # Skip image pulling
```

### Troubleshooting Act

```bash
# If you get Docker socket errors on macOS
act -j test --secret-file .secrets --pull=false --container-daemon-socket /var/run/docker.sock

# For port conflicts, use different ports in .secrets
POSTGRES_PORT=5436
REDIS_PORT=6381
GO_API_PORT=8082
```

## Verification

### Check Database and Cache

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

# Check Redis cache
redis-cli ping
redis-cli info memory
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

2. **Optimize Database**
   ```sql
   -- Increase work_mem for vector operations
   SET work_mem = '256MB';
   ```

3. **Go API Optimization**
   ```bash
   # Set Go environment variables for better performance
   export GOMAXPROCS=4
   export GOGC=100
   ```

## Next Steps

1. **Customize Configuration**: Modify `.env` for your environment
2. **Add Authentication**: Implement API authentication
3. **Scale Deployment**: Use Docker containers for production
4. **Monitor Performance**: Add Prometheus metrics
5. **Add Tests**: Implement comprehensive test suite

## Support

- **Documentation**: [docs/](docs/)
