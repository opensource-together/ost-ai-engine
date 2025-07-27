# Plateforme d'Analyse de repos Git

Un système distribué pour l'analyse automatisée de repos Git qui collecte quotidiennement les données de repos, les traite via des pipelines d'apprentissage automatique, et stocke les insights sémantiques dans une base de données vectorielle pour des requêtes intelligentes.

## 🎯 Aperçu du Projet

Cette plateforme automatise le processus de :
1. **Collecte Quotidienne de Dépôts** - Récupère les données de commits, modifications de fichiers et métadonnées depuis les repos Git configurés
2. **Analyse par IA** - Traite les données Git brutes à travers des modèles d'apprentissage automatique pour extraire des insights
3. **Stockage Vectoriel** - Stocke les données analysées dans une base de données vectorielle pour la recherche sémantique et les requêtes de similarité
4. **Traitement Scalable** - Utilise des files d'attente de tâches distribuées pour gérer efficacement un grand nombre de repos

## 📁 Structure du Projet

```
src/
├── domain/                     # Logique métier centrale (aucune dépendance externe)
│   ├── models/                 # Entités du domaine
│   └── ports/                  # Définitions d'interfaces
├── application/                # Cas d'usage et workflows métier
│   ├── services/               # Services métier centraux
│   └── use_cases/              # Opérations métier spécifiques
├── infrastructure/             # Adaptateurs systèmes externes
│   ├── postgres/               # Persistance base de données
│   ├── redis/                  # File d'attente et cache
│   ├── celery/                 # Traitement tâches distribuées
│   │   ├── app.py              # Configuration application Celery
│   │   ├── config.py           # Configuration Celery
│   ├── scraping/               # Implémentations extraction données
│   └── analysis/               # Implémentations traitement IA
├── api/                        # Interfaces externes
├── config/                     # Gestion configuration
│   ├── config.py             # Paramètres application
└── tests/                      # Suites de tests
    ├── unit/                   # Tests unitaires par couche
    ├── integration/            # Tests d'intégration
    └── fixtures/               # Données de test
```

## 🚀 Démarrage Rapide

### Prérequis

- Python 3.9+
- Conda 24.11
- PostgreSQL 17+
- Redis 6+
- Git

### Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/opensource-together/data-engine
   cd data-engine
   ```

2. **Configurer l'environnement Python**
   ```bash
   conda create -n data-engine python=3.9
   conda activate data-engine
   pip install -r requirements.txt
   ```

3. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos identifiants de base de données et paramètres
   ```

### Configuration

Créer un fichier `.env` avec les paramètres requis :

```env
# Base de données
DATABASE_URL=postgresql://utilisateur:motdepasse@localhost:5432/analyse_git
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_URL=redis://localhost:6379/0

# Analyse IA
VECTOR_DB_TYPE=chromadb  # ou pinecone
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Surveillance
LOG_LEVEL=INFO
FLOWER_PORT=5555
```

## 🧪 Workflow de Développement

### Exécution des Tests

#### Tests Unitaires de l'Infrastructure (76 tests)
```bash
# Tous les tests d'infrastructure
poetry run pytest tests/unit/infrastructure/ -v

# Tests spécifiques par composant
poetry run pytest tests/unit/infrastructure/postgres/ -v      # Database (22 tests)
poetry run pytest tests/unit/infrastructure/scraping/ -v      # GitHub Scraper (12 tests)
poetry run pytest tests/unit/infrastructure/test_config.py -v # Configuration (18 tests)
poetry run pytest tests/unit/infrastructure/analysis/ -v      # Model Persistence (22 tests)
```

#### Tests d'Intégration
```bash
# Tests d'intégration complets
poetry run pytest tests/integration/ -v

# Tests avec couverture
poetry run pytest --cov=src --cov-report=html
```

#### Validation Pré-commit
```bash
# Qualité du code
poetry run ruff check .
poetry run black --check .

# Tests critiques
poetry run pytest tests/unit/infrastructure/ -v
```

**📊 Statut des Tests**: ✅ **76/76 tests d'infrastructure passent**
**📖 Documentation**: Voir [docs/testing_strategy.md](docs/testing_strategy.md) pour les détails

### Étendre les Collecteurs

Pour ajouter le support de nouveaux types de sources :

1. **Créer un nouveau collecteur** dans `infrastructure/scraping/` :
   ```python
   class NouveauCollecteur(Scraper):
       def can_handle(self, source: DataSource) -> bool:
           return source.source_type == SourceType.NOUVEAU_TYPE
       
       def scrape(self, source: DataSource) -> ScrapedData:
           # Implémentation
   ```

2. **L'enregistrer** dans `scraper_factory.py` :
   ```python
   self._scrapers.append(NouveauCollecteur())
   ```

### Ajouter des Étapes d'Analyse IA

1. **Implémenter service d'analyse** dans `infrastructure/analysis/` :
   ```python
   class ServiceAnalysePersonnalisé(AnalysisService):
       def analyze(self, data: ScrapedData) -> AnalysisResult:
           # Votre traitement IA
   ```

2. **Mettre à jour le workflow** pour inclure votre étape d'analyse

## 🔧 Options de Configuration

### Configuration de Collecte de Dépôt

```json
{
  "branch": "main",
  "since_date": "2024-01-01T00:00:00Z",
  "file_extensions": [".py", ".js"],
  "max_commits": 1000,
  "include_merge_commits": false,
  "exclude_paths": ["tests/", "docs/"]
}
```

### Configuration Celery

```python
# Ajuster concurrence workers selon votre système
CELERY_WORKER_CONCURRENCY = 4

# Routage des tâches pour différents types de travail
CELERY_ROUTES = {
    'scraping.*': {'queue': 'scraping'},
    'analysis.*': {'queue': 'analysis'},
}
```
