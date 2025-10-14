DevOps Deployment Guide
=======================

This guide provides all steps for a DevOps engineer to deploy and launch OST AI Engine.

Prerequisites
-------------
- OS: Linux, macOS, or Windows
- Python = 3.13.7
- Docker & Docker Compose
- PostgreSQL (local or Docker)
- Node.js (optionnel pour Prisma)
   .. code-block:: ini

      POSTGRES_DB=db_name
      POSTGRES_USER=db_user
      POSTGRES_PASSWORD=db_password
      DATABASE_URL=postgresql://<db_user>:<db_password>@localhost:port/<db_name>

      GITHUB_ACCESS_TOKEN=your_github_access_token_here
      GITLAB_ACCESS_TOKEN=your_gitlab_access_token_here

Python Dependencies
-------------------
1. Install Poetry if needed:

   .. code-block:: bash

      pip install poetry

2. Install dependencies:

   .. code-block:: bash

      poetry install

3. (Optionnel) Forcer le venv dans le projet:

   .. code-block:: bash

      poetry config virtualenvs.in-project true
      poetry install

Go Dependencies 

1. Install Go (https://go.dev/dl/)  

2. Install Go modules for scrapers:  

   .. code-block:: bash

      cd src/infrastructure/services/go/github
      go mod tidy
      cd ../gitlab
      go mod tidy

Database Setup
--------------
1. Launch PostgreSQL (local or via Docker Compose)
2. Run Prisma migrations if needed (Node.js required):

   .. code-block:: bash

      npm install
      npx prisma migrate deploy

Deployment
----------
1. Start database (Docker Compose):

   .. code-block:: bash

      docker compose up -d

2. Check containers:

   .. code-block:: bash

      docker ps

3. Launch Dagster locally via Poetry:

   .. code-block:: bash

      poetry run dagster dev -m src.dagster.definitions --host 127.0.0.1 --port 3000

   Access Dagster UI: http://localhost:3000

   Le job `github_scraper_job` est automatiquement planifié pour s'exécuter toutes les 6 heures (cron: `6 * * * *`).
   Vous n'avez rien à faire, Dagster lancera ce job selon la planification définie dans `src/dagster/definitions.py`.
   Vous pouvez consulter l'état, les logs et les assets dans l'interface Dagster.


Sphinx Documentation
--------------------
1. Build static HTML:

   .. code-block:: bash

      cd docs
      poetry run sphinx-build -b html . _build

   Open ``_build/index.html`` in browser

2. Live server (auto-reload):

   .. code-block:: bash

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
- Always update ``.env.local`` for secrets
- Use Poetry for Python, Go modules for Go
- Use Docker Compose for orchestration
- Use Dagster UI for pipeline monitoring
