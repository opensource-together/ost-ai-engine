# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the project structure, technologies, and conventions.

## Project Overview

This project is a data engine for analyzing GitHub repositories and providing recommendations. It is a distributed system that collects data from Git repositories, processes it through a machine learning pipeline, and stores the results in a vector database for semantic querying.

The project is built with Python and utilizes a variety of technologies, including:

*   **FastAPI**: For building the recommendation API.
*   **Dagster**: For orchestrating the data pipeline.
*   **dbt**: For data transformation.
*   **SQLAlchemy**: For interacting with the PostgreSQL database.
*   **Celery and Redis**: For distributed task queuing.
*   **scikit-learn and sentence-transformers**: For machine learning and natural language processing.
*   **Poetry**: For dependency management.

The project follows a clean architecture, with the code organized into `domain`, `application`, and `infrastructure` layers.

## Building and Running

### Poetry Scripts

The `pyproject.toml` file defines the following scripts for common development tasks:

*   `poetry run ruff check .`: Check for linting & formatting errors.
*   `poetry run pytest`: Run the test suite.

### Running the Application

To run the application, you need to have Docker and Docker Compose installed. Then, you can use the following command to start the services:

```bash
docker-compose up -d
```

This will start the following services:

*   `postgres`: The PostgreSQL database.
*   `redis`: The Redis server.
*   `api`: The FastAPI application.
*   `worker`: The Celery worker.
*   `dagster`: The Dagster UI.

### Running the Pipeline

The data pipeline can be triggered from the Dagster UI, which is available at `http://localhost:3000`. The main pipeline is called `training_data_pipeline`.

## Development Conventions

### Code Style

The project uses `ruff` for linting. Please ensure that your code conforms to these standards before submitting a pull request.

### Testing

The project has a comprehensive test suite that includes unit tests and integration tests. The tests are located in the `tests` directory. Please add tests for any new code that you add to the project.

### Commit Messages

The project follows the Conventional Commits specification for commit messages. Please format your commit messages according to this specification.
