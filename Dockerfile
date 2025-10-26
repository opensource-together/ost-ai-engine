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
        libgcc-s1 \
        nodejs \
        npm && \
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


# ==============================================================================
# STAGE 2: Go builder - compile Go binaries
# ==============================================================================
FROM golang:1.25.3 AS go-builder

WORKDIR /go

# Copy and build Go services
COPY src/services/go/github/ ./github/
COPY src/services/go/gitlab/ ./gitlab/

RUN cd ./github && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o /go/github-scraper main.go
RUN cd ./gitlab && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o /go/gitlab-scraper main.go


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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PROJECT_ROOT=.
ENV CFG_PATH=config/cfg.py
ENV DAGSTER_HOME=/app/src/dagster
ENV PRISMA_BINARY_CACHE_DIR=/app/.cache/prisma
ENV XDG_CACHE_HOME=/app/.cache
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user for the app
RUN addgroup --system app && adduser --system --group app

# Copy required artifacts from previous stages
COPY --from=builder --chown=app:app /app/pyproject.toml ./pyproject.toml
COPY --chown=app:app docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

COPY --chown=app:app src/dagster/resources/ src/dagster/resources/
COPY --from=builder --chown=app:app /app/.venv .venv
COPY --from=builder --chown=app:app /app/src src

COPY --from=builder --chown=app:app /app/prisma prisma
COPY --from=builder --chown=app:app /app/.cache/prisma /app/.cache/prisma

# Copy helper scripts (cfg_cron, etc.) into the image so entrypoint can start them
COPY --chown=app:app scripts/ /app/scripts/
RUN chmod +x /app/scripts/cfg_cron.py || true

COPY --from=go-builder --chown=app:app /go/github-scraper github-scraper
COPY --from=go-builder --chown=app:app /go/gitlab-scraper gitlab-scraper

# Create cache dirs and set ownership to 'app'
RUN mkdir -p /app/.cache/prisma /app/dagster_home /app/src/dagster && \
    chown -R app:app /app/.cache /app/dagster_home /app/src/dagster

# Create config dir and set owner
RUN mkdir config/ && chown app:app config

# Ensure Go binaries are executable (fix permission issues)
RUN chmod +x /app/github-scraper /app/gitlab-scraper || true

# Switch to non-root user for runtime (safer)
USER app

EXPOSE 3000

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
CMD ["dagster", "dev", "-m", "src.dagster.definitions", "--host", "0.0.0.0", "--port", "3000" ]