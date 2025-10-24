# ========================================
# OST AI ENGINE - DOCKERFILE
# ========================================

# ==============================================================================
# STAGE 1: Builder - Installe les dépendances et construit l'application
# ==============================================================================
FROM python:3.11-slim AS builder

# Installe les dépendances système lourdes, nécessaires uniquement pour la construction
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

# Installe Poetry
RUN pip install poetry==2.2.1

WORKDIR /app

ENV PRISMA_BINARY_CACHE_DIR=/app/.cache/prisma
ENV XDG_CACHE_HOME=/app/.cache
RUN mkdir -p /app/.cache/prisma

# Configure Poetry pour créer l'environnement virtuel dans le projet
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Installe les dépendances Python
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

# Copie le code source et génère le client Prisma
COPY src/ src/
COPY prisma/ prisma/
# Génère le client Prisma et pré-remplit le cache des binaires dans /app/.cache/prisma
RUN poetry run prisma generate
RUN poetry run prisma py fetch


# ==============================================================================
# STAGE 2: Go Builder - Compile les binaires Go
# ==============================================================================
FROM golang:1.25.3 AS go-builder

WORKDIR /go

# Copie et compile les services Go
COPY src/services/go/github/ ./github/
COPY src/services/go/gitlab/ ./gitlab/

RUN cd ./github && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o /go/github-scraper main.go
RUN cd ./gitlab && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o /go/gitlab-scraper main.go


# ==============================================================================
# STAGE 3: Production - Crée l'image finale légère
# ==============================================================================
FROM python:3.11-slim AS production

# Installe UNIQUEMENT les librairies système nécessaires à l'exécution
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        libatomic1 \
        libstdc++6 \
        libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Définit les variables d'environnement
ENV PROJECT_ROOT=.
ENV CFG_PATH=config/cfg.py
ENV DAGSTER_HOME=/app/src/dagster
ENV PRISMA_BINARY_CACHE_DIR=/app/.cache/prisma
ENV XDG_CACHE_HOME=/app/.cache
ENV PATH="/app/.venv/bin:$PATH"

# Crée un utilisateur non-root pour l'application
RUN addgroup --system app && adduser --system --group app

# Copie les artefacts nécessaires depuis les stages précédents
COPY --from=builder --chown=app:app /app/pyproject.toml ./pyproject.toml
COPY --chown=app:app docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

COPY --chown=app:app src/dagster/config/ src/dagster/config
COPY --from=builder --chown=app:app /app/.venv .venv
COPY --from=builder --chown=app:app /app/src src

COPY --from=builder --chown=app:app /app/prisma prisma
COPY --from=builder --chown=app:app /app/.cache/prisma /app/.cache/prisma

COPY --from=go-builder --chown=app:app /go/github-scraper github-scraper
COPY --from=go-builder --chown=app:app /go/gitlab-scraper gitlab-scraper

# crée les dossiers de cache et attribue la propriété à l'utilisateur 'app'
RUN mkdir -p /app/.cache/prisma /app/dagster_home /app/src/dagster && \
    chown -R app:app /app/.cache /app/dagster_home /app/src/dagster

RUN mkdir config/ && chown app:app config

# Ensure Go binaries are executable (fixes exec permission issues when copied)
RUN chmod +x /app/github-scraper /app/gitlab-scraper || true

# Passe à l'utilisateur non-root pour l'exécution (meilleure sécurité)
USER app

EXPOSE 3000

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
CMD ["dagster", "dev", "-m", "src.dagster.definitions", "--host", "0.0.0.0", "--port", "3000" ]