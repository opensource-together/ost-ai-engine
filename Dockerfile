
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

# Build Fetcher
WORKDIR /app/src/services/go/fetcher
RUN go mod download
RUN go build -o /app/bin/ost-fetcher .

# Build Scraper
WORKDIR /app/src/services/go/scraper
RUN go mod download
RUN go build -o /app/bin/ost-scraper .

# ==============================================================================
# Stage 2: Python Builder
# Installs Poetry and exports requirements
# ==============================================================================
FROM python:3.11-slim AS python-builder

WORKDIR /app

# Install poetry
RUN pip install poetry==1.8.2

# Copy configuration
COPY pyproject.toml poetry.lock ./

# Export dependencies to requirements.txt (avoids installing poetry in final image)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# ==============================================================================
# Stage 3: Runtime
# Final lightweight image
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# libpq-dev is needed for psycopg2 (if not binary), git is needed for dbt deps
RUN apt-get update && apt-get install -y \
    libpq-dev \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY --from=python-builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Go binaries from Stage 1
COPY --from=go-builder /app/bin/ost-fetcher /usr/local/bin/ost-fetcher
COPY --from=go-builder /app/bin/ost-scraper /usr/local/bin/ost-scraper

# Copy project code
COPY . .

# Set environment
ENV DAGSTER_HOME=/app/dagster_home
ENV PYTHONPATH=/app
ENV DBT_PROJECT_DIR=/app/dbt

# Initialize dbt
RUN if [ -d "dbt" ]; then cd dbt && dbt deps; fi

# Create Dagster home
RUN mkdir -p $DAGSTER_HOME

# Expose Dagster webserver port
EXPOSE 3000

# Default command: run dagster dev (can be overridden in compose)
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]
