# OST Data Engine Documentation

Welcome to the OST Data Engine documentation. This project implements a machine learning pipeline for GitHub project recommendations using semantic embeddings and similarity calculations.

## Core Components

- **ML Pipeline**: Dagster-based pipeline for data processing and model training
- **Database**: PostgreSQL with pgvector for efficient vector storage and similarity queries
- **API**: Go-based recommendation API for high-performance project suggestions
- **MLflow**: Model tracking and versioning for embeddings and ML artifacts
- **Redis**: Cache layer for ML pipeline optimization
- **dbt**: Data transformation and modeling layer

## Documentation Sections

### Architecture
- [System Overview](architecture/overview.md) - High-level architecture and design decisions
- [Data Flow](architecture/data-flow.md) - How data moves through the system
- [Technology Stack](architecture/technology-stack.md) - Detailed technology choices

### Development
- [Setup Guide](development/setup.md) - Local development environment setup
- [Code Structure](development/code-structure.md) - Project organization and conventions
- [Testing](testing/overview.md) - Testing strategy and test organization
- [dbt Test Models](testing/dbt-test-models.md) - Test data management with dbt
- [Test Scripts](testing/scripts.md) - Testing scripts and utilities

### Deployment
- [Environment Configuration](deployment/environment.md) - Environment variables and configuration
- [Quick Start](deployment/quick-start.md) - Fast deployment guide
- [GitHub Secrets](deployment/github-secrets.md) - CI/CD secrets management
- [Go API Setup](deployment/go-api-setup.md) - Go API deployment and configuration

### ML Pipeline
- [Pipeline Overview](ml-pipeline/overview.md) - Dagster pipeline architecture
- [Model Management](ml-pipeline/models.md) - MLflow model tracking
- [Embeddings](ml-pipeline/embeddings.md) - Semantic and hybrid embeddings

### API
- [Go API](api/go-api.md) - Go recommendation API documentation
- [Endpoints](api/endpoints.md) - API endpoint specifications
- [Examples](api/examples.md) - API usage examples and patterns

### Database
- [Schema Documentation](database/schema.md) - Complete database schema and relationships

## Quick Links

- [Local Testing with Act](deployment/github-secrets.md#local-testing-with-act) - Test CI locally
- [Environment Variables](deployment/environment.md) - All configuration options
- [Test Structure](testing/overview.md) - Testing organization and best practices
- [dbt Test Models](testing/dbt-test-models.md) - Test data management
- [API Examples](api/examples.md) - Practical API usage examples

## Getting Started

1. **Setup Environment**: Follow the [Quick Start Guide](deployment/quick-start.md)
2. **Run Tests**: Use the [Testing Documentation](testing/overview.md)
3. **Deploy**: Configure [GitHub Secrets](deployment/github-secrets.md) for CI/CD
4. **Test API**: Check [API Examples](api/examples.md) for usage patterns

## Contributing

Please refer to the [Development Guide](development/setup.md) for contribution guidelines and local setup instructions.
