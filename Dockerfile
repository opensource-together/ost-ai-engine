# ========================================
# OST AI ENGINE - DAGSTER + GO DOCKERFILE
# ========================================
FROM python:3.13-slim AS base

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
        gcc \
        libpq-dev \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Go (for Go scrapers)
ENV GO_VERSION=1.22.3
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:$PATH"

# Install Poetry
RUN pip install poetry

# Set workdir
WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

# Copy all source code (Python + Go)
COPY src/ src/
COPY prisma/ prisma/
COPY .env .env

# Set Dagster home
ENV DAGSTER_HOME=/app/src/dagster

# Expose Dagster UI port
EXPOSE 3000

# Entrypoint: launch Dagster webserver
CMD ["poetry", "run", "dagster", "dev", "-m", "src.dagster.definitions", "--host", "0.0.0.0", "--port", "3000"]
