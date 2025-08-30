# Environment Configuration

## Overview

The OST Data Engine uses environment variables for all configuration. This ensures flexibility across different environments and follows security best practices.

## Configuration File

Copy the example environment file and configure it for your environment:

```bash
cp .env.example .env
```

## Environment Variables

### Database Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DATABASE_URL` | `postgresql://user:password@localhost:5434/OST_PROD` | PostgreSQL connection string | Yes |
| `POSTGRES_USER` | `user` | PostgreSQL username | Yes |
| `POSTGRES_PASSWORD` | `password` | PostgreSQL password | Yes |
| `POSTGRES_DB` | `OST_PROD` | PostgreSQL database name | Yes |
| `DB_HOST` | `localhost` | Database host | Yes |
| `DB_PORT` | `5434` | Database port | Yes |
| `DB_SCHEMA` | `public` | Database schema | No |
| `DB_THREADS` | `4` | Number of database threads | No |

### dbt Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DBT_PROJECT_DIR` | `src/dbt` | dbt project directory | Yes |

### Go API Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `GO_API_PORT` | `8080` | Go API port | No |

### Redis Cache Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `REDIS_CACHE_URL` | `redis://localhost:6379/0` | Redis connection URL for ML pipeline cache | Yes |
| `REDIS_CACHE_TTL` | `86400` | Cache TTL in seconds (24h) for embeddings | No |
| `REDIS_PORT` | `6379` | Redis port for Docker service | No |

### ML Model Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `MODEL_DIR` | `models/` | Model directory | No |
| `MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Model name | Yes |
| `MODEL_DISPLAY_NAME` | `all-MiniLM-L6-v2` | Model display name | No |
| `MODEL_DIMENSIONS` | `384` | Model embedding dimensions | Yes |

### Recommendation Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `RECOMMENDATION_SEMANTIC_WEIGHT` | `0.25` | Weight for semantic similarity | No |
| `RECOMMENDATION_CATEGORY_WEIGHT` | `0.45` | Weight for category similarity | No |
| `RECOMMENDATION_TECH_WEIGHT` | `0.5` | Weight for tech stack similarity | No |
| `RECOMMENDATION_POPULARITY_WEIGHT` | `0.1` | Weight for popularity score | No |
| `RECOMMENDATION_TOP_N` | `5` | Number of recommendations to return | No |
| `RECOMMENDATION_MIN_SIMILARITY` | `0.1` | Minimum similarity threshold | No |
| `RECOMMENDATION_MAX_PROJECTS` | `1000` | Maximum projects to consider | No |
| `RECOMMENDATION_POPULARITY_THRESHOLD` | `100000` | Popularity threshold for normalization | No |



### MLflow Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `MLFLOW_TRACKING_URI` | `sqlite:///logs/mlflow.db` | MLflow tracking URI | No |
| `MLFLOW_ARTIFACT_ROOT` | `models/mlruns` | MLflow artifact root | No |
| `MLFLOW_MODEL_REGISTRY_NAME` | `ost-models` | MLflow model registry name | No |
| `MLFLOW_UI_PORT` | `5050` | MLflow UI port | No |
| `MLFLOW_UI_HOST` | `0.0.0.0` | MLflow UI host | No |

### Dagster Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `DAGSTER_HOME` | `{PROJECT_ROOT}/logs/dagster` | Dagster home directory | Yes |

### GitHub Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `GITHUB_ACCESS_TOKEN` | `github_pat_...` | GitHub access token | Yes |
| `GITHUB_SCRAPING_QUERY` | `language:python stars:>100...` | GitHub scraping query | No |
| `GITHUB_MAX_REPOSITORIES` | `1000` | Maximum repositories to scrape | No |
| `GITHUB_MIN_STARS` | `100` | Minimum stars for repositories | No |
| `GITHUB_LANGUAGES` | `python,javascript,go,java,rust,typescript` | Languages to scrape | No |

### Security Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `SECRET_KEY` | `your_secret_key_here` | Secret key for security | Yes |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts | No |

### Monitoring Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `ENABLE_METRICS` | `true` | Enable metrics collection | No |
| `METRICS_PORT` | `9090` | Metrics port | No |
| `LOG_LEVEL` | `INFO` | Logging level | No |
| `ENVIRONMENT` | `development` | Environment name | No |

### Application Configuration

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `PROJECT_ROOT` | `./` | Project root directory | Yes |

## Environment-Specific Configurations

### Development Environment

```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:password@localhost:5434/OST_PROD
REDIS_CACHE_URL=redis://localhost:6379/0
GO_API_PORT=8080
```

### Production Environment

```env
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod_user:secure_password@prod-db:5432/OST_PROD
REDIS_CACHE_URL=redis://redis:6379/0
GO_API_PORT=8080
SECRET_KEY=your_very_secure_secret_key_here
```

### Testing Environment

```env
ENVIRONMENT=testing
LOG_LEVEL=INFO
DATABASE_URL=postgresql://test_user:test_password@localhost:5435/OST_TEST
REDIS_CACHE_URL=redis://localhost:6379/0
GO_API_PORT=8081
```

## Validation

### Required Variables Check

Create a validation script to ensure all required variables are set:

```bash
#!/bin/bash
required_vars=(
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
    "MODEL_NAME"
    "MODEL_DIMENSIONS"
    "GITHUB_ACCESS_TOKEN"
    "SECRET_KEY"
    "REDIS_CACHE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is required but not set"
        exit 1
    fi
done

echo "All required environment variables are set"
```

### Environment Validation

```bash
# Validate database connection
psql $DATABASE_URL -c "SELECT 1;" || echo "Database connection failed"

# Validate Redis connection
redis-cli -u $REDIS_CACHE_URL ping || echo "Redis connection failed"


```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong passwords** for database
3. **Rotate secrets regularly** in production
4. **Use environment-specific configurations**
5. **Validate all inputs** from environment variables
6. **Use secrets management** in production (AWS Secrets Manager, HashiCorp Vault, etc.)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` format
   - Verify database is running
   - Check firewall settings

2. **Go API Connection Failed**
   - Verify Go API is running on correct port
   - Check `GO_API_PORT` configuration
   - Validate database connection from Go API

3. **Model Loading Failed**
   - Check `MODEL_NAME` is valid
   - Verify model files exist
   - Check `MODEL_DIMENSIONS` matches model

4. **Go API Not Starting**
   - Check port availability (default: 8080)
   - Verify all required variables are set
   - Check Go API logs for errors
   - Ensure database is accessible from Go API

5. **Redis Cache Issues**
   - Verify Redis service is running
   - Check `REDIS_CACHE_URL` format
   - Validate Redis connection from ML pipeline
   - Check Redis logs for errors
