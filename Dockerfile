# ========================================
# OST AI ENGINE - DAGSTER + GO DOCKERFILE
# ========================================
FROM python:3.11-slim AS builder

# Install build-time system dependencies
# libpq-dev is needed to build psycopg2, git/curl might be needed by poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        git \
        curl

RUN pip install poetry==2.2.1

WORKDIR /app

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

COPY src/ src/
COPY prisma/ prisma/

# Génère le client Prisma Python
RUN poetry run prisma generate


FROM golang:1.25.3-alpine AS go-builder

WORKDIR /go

# Copy only the Go source code needed for the scraper
COPY src/services/go/github/ ./github/
COPY src/services/go/gitlab/ ./gitlab/

RUN cd ./github && go build -o /go/github-scraper main.go
RUN cd ./gitlab && go build -o /go/gitlab-scraper main.go


FROM python:3.11-slim AS production

# libpq5 is the runtime library for PostgreSQL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

ENV PROJECT_ROOT=.
ENV CFG_PATH=config/cfg.py
ENV DAGSTER_HOME=/app/src/dagster

RUN addgroup --system app && adduser --system --group app

COPY --chown=app:app docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
RUN mkdir config/ && chown app:app config
COPY --chown=app:app src/dagster/config/ src/dagster/config
COPY --from=builder --chown=app:app /app/.venv .venv
COPY --from=builder --chown=app:app /app/src src
COPY --from=go-builder --chown=app:app /go/github-scraper github-scraper
COPY --from=go-builder --chown=app:app /go/gitlab-scraper gitlab-scraper

ENV PATH="/app/.venv/bin:$PATH"

# A CHANGER
# USER app
USER root

EXPOSE 3000

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
CMD ["dagster", "dev", "-m", "src.dagster.definitions", "--host", "0.0.0.0", "--port", "3000" ]
