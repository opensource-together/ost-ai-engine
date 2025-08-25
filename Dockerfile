# --- 1. Builder Stage ---
# This stage installs dependencies using Poetry and creates a virtual environment.
FROM python:3.13-slim as builder

# Set the working directory
WORKDIR /app

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry

# Copy only the files needed to install dependencies
# This leverages Docker's layer caching. The layer will only be rebuilt
# if these files change.
COPY poetry.lock pyproject.toml ./

# Configure poetry to create the virtualenv in the project's root
RUN poetry config virtualenvs.in-project true

# Install dependencies into a virtual environment
# We are installing all dependencies for now to ensure the build passes.
# --no-root: Don't install the project itself, just the dependencies
RUN poetry install --no-root --no-dev

# --- 2. Final Stage ---
# This stage creates the final, lean production image.
FROM python:3.13-slim

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Set the PATH to include the virtual environment's binaries
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code
COPY src/ ./src/

# Copy configuration files
COPY pyproject.toml poetry.lock ./

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for the API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command to run the API server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"] 