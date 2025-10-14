Deployment
==========

1. Lancer la base de données et Dagster via Docker Compose :
   docker compose up -d
2. Accéder à l’interface Dagster : http://localhost:3000
3. Vérifier la connexion à la base PostgreSQL
4. Lancer les scrapers Go si besoin :
   go run src/infrastructure/services/go/github/main.go
   go run src/infrastructure/services/go/gitlab/main.go
