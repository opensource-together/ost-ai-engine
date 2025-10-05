# --- 1. Builder Stage ---
FROM python:3.13-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    DAGSTER_HOME=/opt/dagster/dagster_home

WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Go (detect architecture)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        GO_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        GO_ARCH="arm64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -L "https://go.dev/dl/go1.22.4.linux-${GO_ARCH}.tar.gz" | tar -xzC /usr/local
ENV PATH="/usr/local/go/bin:$PATH"

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies with optimizations
# Ensure Poetry creates venv inside project and persist it in the image
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-root --only main --no-ansi \
    && rm -rf $POETRY_CACHE_DIR

# Make venv binaries available on PATH in builder image
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code and configuration files to builder stage
COPY src/ ./src/
COPY workspace.yaml ./
COPY dagster.yaml ./

# Build Go scrapers for Linux
RUN cd src/infrastructure/services/go/github && go build -o scraper main.go
RUN cd src/infrastructure/services/go/gitlab && go build -o scraper main.go

# Create dagster home and copy configuration to the correct location  
RUN mkdir -p $DAGSTER_HOME \
    && cp /app/dagster.yaml $DAGSTER_HOME/dagster.yaml \
    && cp /app/workspace.yaml $DAGSTER_HOME/workspace.yaml \
    && groupadd -r appuser \
    && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app $DAGSTER_HOME

USER appuser

EXPOSE 3000

# Default command for builder stage
CMD ["python", "-c", "import dagster; print('Dagster ready')"]

# --- 2. Final Stage (for production) ---
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DAGSTER_HOME=/opt/dagster \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code and configuration files
COPY src/ ./src/
COPY workspace.yaml ./

# Create dagster home and user in one layer
RUN mkdir -p $DAGSTER_HOME \
    && groupadd -r appuser \
    && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app $DAGSTER_HOME

USER appuser

EXPOSE 3000

# Optimized startup command
CMD ["python", "-c", "import dagster; print('Dagster ready')"]