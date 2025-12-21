# ========================================
# OST AI ENGINE - DOCKERFILE
# ========================================

# ==============================================================================
# STAGE 1: Builder - install build deps and build the app
# ==============================================================================
FROM python:3.11-slim AS builder

# Install heavy system packages required only for build
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    git \
    curl \
    ca-certificates \
    libpq5 \
    libatomic1 \
    libstdc++6 \
    libgcc-s1 && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.2.1

WORKDIR /app

ENV PRISMA_BINARY_CACHE_DIR=/app/.cache/prisma
ENV XDG_CACHE_HOME=/app/.cache
RUN mkdir -p /app/.cache/prisma

# Configure Poetry to create the virtualenv inside the project
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

# Copy source and generate Prisma client
# Generate Prisma client and prefetch binaries into /app/.cache/prisma
COPY src/ src/
COPY dbt/ dbt/
COPY prisma/ prisma/
# Generate Prisma client and prefetch binaries into /app/.cache/prisma
RUN poetry run prisma generate
RUN poetry run prisma py fetch

RUN mkdir -p /app/models && \
    curl -fL -o /app/models/lid.176.ftz https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

# Pre-download embedding models
ENV SENTENCE_TRANSFORMERS_HOME=/app/models/sentence-transformers
COPY scripts/download_models.py /app/scripts/
RUN poetry run python /app/scripts/download_models.py

# ==============================================================================
# STAGE 2: Go builder - compile Go binaries
# ==============================================================================
FROM golang:1.25.3 AS go-builder

WORKDIR /go

# Build args/env for proxy and module fetching
ARG GOPROXY=https://proxy.golang.org,direct
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV GOPROXY=${GOPROXY}
ENV CGO_ENABLED=0
ENV GOOS=linux
ENV GOARCH=amd64
ENV GOTOOLCHAIN=auto

# Copy sources
COPY src/services/go/scraper/ /go/scraper/

# Build binaries (modules will be fetched automatically by go build)
WORKDIR /go/scraper
RUN go build -ldflags="-s -w" -o /go/github-scraper .

# ==============================================================================
# STAGE 3: Production - create lightweight final image
# ==============================================================================
FROM python:3.11-slim AS production

# Install only runtime system libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    libatomic1 \
    libstdc++6 \
    libgcc-s1 \
    ca-certificates \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PROJECT_ROOT=.
ENV CFG_PATH=config/cfg.py
ENV OST_CONFIG_PATH=/app/config/cfg.yaml
ENV DAGSTER_HOME=/app/dagster
ENV DAGSTER_STORAGE_DIR=/app/dagster/history
ENV DAGSTER_LOGS_DIR=/app/dagster/logs
ENV PRISMA_BINARY_CACHE_DIR=/app/.cache/prisma
ENV XDG_CACHE_HOME=/app/.cache

# Configure Poetry to create the virtualenv inside the project
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="/app/.venv/bin:/app/node_modules/.bin:$PATH"

# Create a non-root user for the app
RUN addgroup --system app && adduser --system --group app

# Copy project configuration
COPY --from=builder --chown=app:app /app/pyproject.toml ./pyproject.toml
COPY --from=builder --chown=app:app /app/poetry.lock ./poetry.lock

# Copy Node configuration and install dependencies
COPY --chown=app:app package.json package-lock.json ./
RUN npm ci


# Reuse the virtualenv built in the builder stage (no reinstall here)
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy required artifacts from previous stages
COPY --chown=app:app src/pipeline/resources/ src/pipeline/resources/
COPY --from=builder --chown=app:app /app/src src
COPY --from=builder --chown=app:app /app/dbt dbt

COPY --from=builder --chown=app:app /app/prisma prisma
COPY --from=builder --chown=app:app /app/.cache/prisma /app/.cache/prisma
RUN npx prisma generate

COPY --from=builder --chown=app:app /app/models /app/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/models/sentence-transformers

# Copy helper scripts
COPY --chown=app:app scripts/ /app/scripts/
# Make entrypoint and helper scripts executable
RUN chmod +x /app/scripts/cfg_cron.py /app/scripts/docker-entrypoint.sh || true

COPY --from=go-builder --chown=app:app /go/github-scraper github-scraper

# Create cache dirs and set ownership to 'app'
RUN mkdir -p /app/.cache/prisma /app/dagster /app/src/pipeline ${DAGSTER_STORAGE_DIR} ${DAGSTER_LOGS_DIR} && \
    chown -R app:app /app/.cache /app/dagster /app/src/pipeline ${DAGSTER_STORAGE_DIR} ${DAGSTER_LOGS_DIR}

# Create config dir and set owner
RUN mkdir config/ && chown app:app config

# Ensure Go binaries are executable (fix permission issues)
RUN chmod +x /app/github-scraper || true

# Switch to non-root user for runtime (safer)
USER app

EXPOSE 3000

ENTRYPOINT [ "/app/scripts/docker-entrypoint.sh" ]
CMD ["dagster", "dev", "-m", "src.pipeline.definitions", "--host", "0.0.0.0", "--port", "3000" ]
