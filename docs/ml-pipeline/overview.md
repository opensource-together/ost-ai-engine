# ML Pipeline Overview

## Architecture

The ML Pipeline is built using **Dagster** and orchestrates the entire machine learning workflow from data ingestion to similarity calculations.

```
GitHub Data → Embeddings → Similarities → Storage
```

## Pipeline Components

### 1. Data Ingestion
- **GitHub Scraping**: Collects repository data from GitHub API
- **Data Validation**: Ensures data quality and completeness
- **Storage**: Stores raw data in PostgreSQL

### 2. Embedding Generation
- **User Embeddings**: Generates 384-dimensional embeddings for users
- **Project Embeddings**: Generates 384-dimensional embeddings for projects
- **Hybrid Embeddings**: Combines semantic and structured features

### 3. Similarity Calculations
- **Data Preparation**: dbt models prepare data for similarity calculations
- **Similarity Computation**: Calculates user-project similarities using multiple metrics
- **Storage**: Stores top-N similarities per user

## Dagster Assets

### Core Assets

| Asset | Description | Dependencies |
|-------|-------------|--------------|
| `github_data_ready` | Validates GitHub data availability | None |
| `github_scraping` | Scrapes GitHub repositories | `github_data_ready` |
| `dbt_projects_asset` | Runs dbt project models | `github_scraping` |
| `dbt_project_enriched_data_asset` | Prepares project data for embeddings | `dbt_projects_asset` |
| `project_semantic_embeddings_asset` | Generates semantic embeddings | `dbt_project_enriched_data_asset` |
| `project_hybrid_embeddings_asset` | Generates hybrid embeddings | `project_semantic_embeddings_asset` |
| `dbt_user_embeddings_data_asset` | Prepares user data for embeddings | `project_hybrid_embeddings_asset` |
| `user_embeddings` | Generates user embeddings | `dbt_user_embeddings_data_asset` |
| `dbt_user_project_similarities_asset` | Prepares similarity data | `user_embeddings` |
| `user_project_similarities_asset` | Calculates and stores similarities | `dbt_user_project_similarities_asset` |

### Asset Groups

- **`github_data`**: GitHub data collection and validation
- **`ml_preparation`**: Data preparation using dbt
- **`ml_embeddings`**: Embedding generation
- **`ml_similarities`**: Similarity calculations

## Execution Flow

### 1. Data Pipeline
```bash
# Run GitHub scraping
dagster asset materialize --select github_scraping
```

### 2. Embedding Pipeline
```bash
# Generate project embeddings
dagster asset materialize --select project_hybrid_embeddings

# Generate user embeddings
dagster asset materialize --select user_embeddings
```

### 3. Similarity Pipeline
```bash
# Calculate similarities
dagster asset materialize --select user_project_similarities
```

### 4. Full Pipeline
```bash
# Run complete pipeline
dagster job execute -j training_data_pipeline
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | Embedding model name | `sentence-transformers/all-MiniLM-L6-v2` |
| `MODEL_DIMENSIONS` | Embedding dimensions | `384` |
| `RECOMMENDATION_TOP_N` | Number of recommendations | `5` |
| `RECOMMENDATION_MIN_SIMILARITY` | Minimum similarity threshold | `0.1` |

### Similarity Weights

| Component | Weight | Description |
|-----------|--------|-------------|
| Semantic | 0.25 | Embedding-based similarity |
| Category | 0.45 | Category overlap |
| Tech Stack | 0.5 | Technology overlap |
| Popularity | 0.1 | Project popularity |

## Performance

### Processing Times

- **GitHub Scraping**: ~5-10 minutes (1000 repositories)
- **Embedding Generation**: ~2-5 minutes per asset
- **Similarity Calculation**: ~30-60 seconds (10 users × 979 projects)

### Resource Usage

- **Memory**: ~2-4GB RAM during embedding generation
- **CPU**: Multi-threaded processing for embeddings
- **Storage**: ~100MB for embeddings, ~1MB for similarities

## Monitoring

### Dagster UI

Access the Dagster UI to monitor pipeline execution:

```bash
dagster dev
```

Navigate to `http://localhost:3000` to view:
- Asset materialization status
- Execution logs
- Performance metrics
- Error tracking

### Logging

All assets include comprehensive logging:

```python
log.info(f"🚀 Starting User↔Project similarity calculations")
log.info(f"📊 Loaded {len(user_embeddings_dict)} user embeddings")
log.info(f"✅ Similarity calculation completed!")
```

## Error Handling

### Common Issues

1. **Model Loading Failures**
   - Check `MODEL_NAME` is valid
   - Verify internet connection for model download
   - Check available disk space

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string format
   - Validate user permissions

3. **Memory Issues**
   - Reduce batch sizes
   - Increase system memory
   - Use smaller embedding models

### Recovery

```bash
# Retry failed asset
dagster asset materialize --select failed_asset_name

# Clear and restart
dagster asset materialize --select user_project_similarities --force
```

## Scaling

### Horizontal Scaling

- **Multiple Workers**: Run Dagster with multiple workers
- **Database Sharding**: Partition data across multiple databases
- **Caching**: Use Redis for intermediate results

### Vertical Scaling

- **Larger Instances**: Increase CPU and memory
- **GPU Acceleration**: Use GPU for embedding generation
- **SSD Storage**: Faster I/O for large datasets

## Best Practices

1. **Incremental Processing**: Use Dagster's incremental assets
2. **Data Validation**: Validate data at each step
3. **Error Recovery**: Implement proper error handling
4. **Monitoring**: Monitor resource usage and performance
5. **Testing**: Test pipeline components individually
6. **Documentation**: Document all configuration changes
