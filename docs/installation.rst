Installation
============

Prerequisites:
- Python >= 3.13
- Go >= 1.20
- Docker & Docker Compose
- PostgreSQL

Setup:
1. Clone the repository
2. Copier `.env.example` en `.env.local` et renseigner les clés
3. Installer les dépendances Python :
   poetry install
4. Installer les dépendances Go (dans src/infrastructure/services/go/*)
   go mod tidy
