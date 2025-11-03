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
COPY prisma/ prisma/
# Generate Prisma client and prefetch binaries into /app/.cache/prisma
RUN poetry run prisma generate
RUN poetry run prisma py fetch

RUN mkdir -p /app/models && \
    curl -fL -o /app/models/lid.176.ftz https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

# ==============================================================================
# STAGE 2: Go builder - compile Go binaries
# ==============================================================================
FROM golang:1.22 AS go-builder

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

# Layered module download for better caching (GitHub)
COPY src/services/go/github/go.mod ./github/go.mod
COPY src/services/go/github/go.sum ./github/go.sum
RUN cd ./github && go mod download

# Layered module download for better caching (GitLab)
COPY src/services/go/gitlab/go.mod ./gitlab/go.mod
COPY src/services/go/gitlab/go.sum ./gitlab/go.sum
RUN cd ./gitlab && go mod download

# Copy sources
COPY src/services/go/github/ ./github/
COPY src/services/go/gitlab/ ./gitlab/

# Build binaries
RUN cd ./github && go build -ldflags="-s -w" -o /go/github-scraper .
RUN cd ./gitlab && go build -ldflags="-s -w" -o /go/gitlab-scraper .


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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PROJECT_ROOT=.
ENV CFG_PATH=config/cfg.py
ENV OST_CONFIG_PATH=/app/config/cfg.yaml
ENV DAGSTER_HOME=/app/.dagster_home
ENV DAGSTER_STORAGE_DIR=/app/.dagster_home/history
ENV DAGSTER_LOGS_DIR=/app/.dagster_home/logs
ENV PRISMA_BINARY_CACHE_DIR=/app/.cache/prisma
ENV XDG_CACHE_HOME=/app/.cache

# Configure Poetry to create the virtualenv inside the project
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user for the app
RUN addgroup --system app && adduser --system --group app

# Copy project configuration
COPY --from=builder --chown=app:app /app/pyproject.toml ./pyproject.toml
COPY --from=builder --chown=app:app /app/poetry.lock ./poetry.lock

# Reuse the virtualenv built in the builder stage (no reinstall here)
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy required artifacts from previous stages
COPY --chown=app:app src/pipeline/resources/ src/pipeline/resources/
COPY --from=builder --chown=app:app /app/src src

COPY --from=builder --chown=app:app /app/prisma prisma
COPY --from=builder --chown=app:app /app/.cache/prisma /app/.cache/prisma

COPY --from=builder --chown=app:app /app/models /app/models

# Copy helper scripts
COPY --chown=app:app scripts/ /app/scripts/
# Make entrypoint and helper scripts executable
RUN chmod +x /app/scripts/cfg_cron.py /app/scripts/docker-entrypoint.sh || true

COPY --from=go-builder --chown=app:app /go/github-scraper github-scraper
COPY --from=go-builder --chown=app:app /go/gitlab-scraper gitlab-scraper

# Create cache dirs and set ownership to 'app'
RUN mkdir -p /app/.cache/prisma /app/.dagster_home /app/src/pipeline ${DAGSTER_STORAGE_DIR} ${DAGSTER_LOGS_DIR} && \
    chown -R app:app /app/.cache /app/.dagster_home /app/src/pipeline ${DAGSTER_STORAGE_DIR} ${DAGSTER_LOGS_DIR}

# Create config dir and set owner
RUN mkdir config/ && chown app:app config

# Ensure Go binaries are executable (fix permission issues)
RUN chmod +x /app/github-scraper /app/gitlab-scraper || true

# Switch to non-root user for runtime (safer)
USER app

EXPOSE 3000

ENTRYPOINT [ "/app/scripts/docker-entrypoint.sh" ]
CMD ["dagster", "dev", "-m", "src.pipeline.definitions", "--host", "0.0.0.0", "--port", "3000" ]
