Deployment
==========

Aperçu
------
- Docker Compose démarre la base PostgreSQL (port 7777 -> 5432).
- Dagster Web UI est lancé en local via Poetry (port 3000).

1) Démarrer PostgreSQL (Docker)
-------------------------------

.. code-block:: powershell

   docker compose up -d

Vérifier que le conteneur est UP :

.. code-block:: powershell

   docker ps

2) Lancer Dagster (local)
-------------------------

.. code-block:: powershell

   # Depuis la racine du repo
   poetry install
   poetry run dagster dev -m src.dagster.definitions --host 127.0.0.1 --port 3000

Accéder à l’interface Dagster : http://localhost:3000

3) Lancer les scrapers Go (optionnel)
-------------------------------------
Assurez-vous que les variables d’environnement (tokens) sont présentes dans la session.

.. code-block:: powershell

   # GitHub
   go run src/infrastructure/services/go/github/main.go

   # GitLab
   go run src/infrastructure/services/go/gitlab/main.go

4) Vérifications
----------------
- Connexion DB : test via un client Postgres (localhost:7777, user/db/password de .env.local)
- Pipelines Dagster : consulter les assets/jobs dans l’UI
