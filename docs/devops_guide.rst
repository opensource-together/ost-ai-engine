DevOps Deployment Guide
=======================

This guide provides all steps for a DevOps engineer to deploy and launch OST AI Engine.

Prerequisites
-------------
- OS: Linux, macOS, or Windows
- Python >= 3.13
- Go >= 1.20
- Docker & Docker Compose
- PostgreSQL (local or Docker)
- Node.js (optionnel pour Prisma)

Environment Configuration
------------------------
1. Copy `.env.example` to `.env.local` and fill in required secrets (DB, GitHub/GitLab tokens).
2. Example (put in `.env.local`):

   .. code-block:: ini

      DATABASE_URL=postgresql://ai-engine:ai-engine@localhost:7777/ai-engine
      POSTGRES_DB=ai-engine
      POSTGRES_USER=ai-engine
      POSTGRES_PASSWORD=ai-engine
      GITHUB_ACCESS_TOKEN=your_github_access_token_here
      GITLAB_ACCESS_TOKEN=your_gitlab_access_token_here

Python Dependencies
-------------------
1. Install Poetry if needed:

   .. code-block:: powershell

      pip install poetry

2. Install dependencies:

   .. code-block:: powershell

      poetry install

3. (Optionnel) Forcer le venv dans le projet:

   .. code-block:: powershell

      poetry config virtualenvs.in-project true
      poetry install

Go Dependencies
---------------
1. Install Go (https://go.dev/dl/)
2. Install Go modules for scrapers:

   .. code-block:: powershell

      cd src/infrastructure/services/go/github
      go mod tidy
      cd ../gitlab
      go mod tidy

Database Setup
--------------
1. Launch PostgreSQL (local or via Docker Compose)
2. Run Prisma migrations if needed (Node.js required):

   .. code-block:: powershell

      cd prisma
      npm install
      npx prisma migrate deploy

Deployment
----------
1. Start database (Docker Compose):

   .. code-block:: powershell

      docker compose up -d

2. Check containers:

   .. code-block:: powershell

      docker ps
3. Launch Dagster locally via Poetry:

   .. code-block:: powershell

      poetry run dagster dev -m src.dagster.definitions --host 127.0.0.1 --port 3000

   Access Dagster UI: http://localhost:3000

Go Scrapers
-----------
1. To run scrapers manually:

   .. code-block:: powershell

      # GitHub
      go run src/infrastructure/services/go/github/main.go

      # GitLab
      go run src/infrastructure/services/go/gitlab/main.go

Sphinx Documentation
--------------------
1. Build static HTML:

   .. code-block:: powershell

      cd docs
      poetry run sphinx-build -b html . _build

   Open ``_build/index.html`` in browser

2. Live server (auto-reload):

   .. code-block:: powershell

      poetry run sphinx-autobuild . _build

   Open http://localhost:8000

Monitoring & Debug
------------------
- Check logs: ``docker compose logs``
- Restart services: ``docker compose restart``
- Check DB: connect to PostgreSQL with admin tool
- Check Dagster jobs in UI

Tips
----
- Always update `.env.local` for secrets
- Use Poetry for Python, Go modules for Go
- Use Docker Compose for orchestration
- Use Dagster UI for pipeline monitoring
