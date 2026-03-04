
# ==============================================================================
# Stage 1: Go Builder
# Compiles the separate Go services (fetcher and scraper)
# ==============================================================================
FROM golang:1.24-alpine AS go-builder

WORKDIR /app

# Copy Go service definitions
# We assume the structure: src/services/go/{service}/go.mod
COPY src/services/go/fetcher ./src/services/go/fetcher
COPY src/services/go/scraper ./src/services/go/scraper

# Build Scraper
WORKDIR /app/src/services/go/scraper
RUN CGO_ENABLED=0 go mod download && go build -ldflags="-s -w" -o /app/bin/ost-scraper .

# Build Fetcher
WORKDIR /app/src/services/go/fetcher
RUN CGO_ENABLED=0 go mod download && go build -ldflags="-s -w" -o /app/bin/ost-fetcher .

# ==============================================================================
# Stage 2: Python Builder
# Exports requirements via uv
# ==============================================================================
FROM python:3.11-slim AS python-builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv export --frozen --no-dev --no-hashes --output-file requirements.txt

# ==============================================================================
# Stage 3: Runtime
# Final lightweight image
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# libpq-dev: psycopg2, git: dbt deps, curl: healthcheck, g++: fasttext C++ extension
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    git \
    curl \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Strip the `-e .` editable self-install line — the project is COPY'd later and
# discovered via PYTHONPATH, so there's no need for an editable install.
COPY --from=python-builder /app/requirements.txt .
RUN sed -i '/^-e \./d' requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

# Copy Go binaries from Stage 1
COPY --from=go-builder /app/bin/ost-fetcher /usr/local/bin/ost-fetcher
COPY --from=go-builder /app/bin/ost-scraper /usr/local/bin/ost-scraper

# Copy project code
COPY . .

# Set environment
ENV DAGSTER_HOME=/app/dagster_home
ENV DAGSTER_STORAGE_DIR=/app/dagster_home/storage
ENV DAGSTER_LOGS_DIR=/app/dagster_home/logs
ENV PYTHONPATH=/app
ENV DBT_PROJECT_DIR=/app/dbt

# Create Dagster home, copy prod config as default
RUN mkdir -p $DAGSTER_HOME \
    && cp dagster.prod.yaml $DAGSTER_HOME/dagster.yaml

# Create non-root user and set ownership for writable directories
RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -s /bin/bash appuser \
    && chown -R appuser:appuser $DAGSTER_HOME /app/dbt /app/models /app/scripts

USER appuser

# Expose Dagster webserver port
EXPOSE 3000

# Healthcheck for Dagster webserver
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:3000/server_info || exit 1

# Default command: run dagster-webserver (production mode)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000", "-w", "/app/workspace.yaml"]
