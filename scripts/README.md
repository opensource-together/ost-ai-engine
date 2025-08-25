# 📁 Scripts Database

Ce dossier contient les scripts essentiels pour la gestion de la base de données.

## 🗂️ Structure

```
scripts/
├── database/
│   ├── clean_tables.sql          # Nettoyer les tables opérationnelles
│   ├── create_test_users.py      # Créer des utilisateurs de test
│   ├── recreate_schema.sql       # Recréer le schéma complet (SQL)
│   └── recreate_schema.py        # Recréer le schéma complet (Python)
└── README.md                     # Cette documentation
```

## 📋 Scripts disponibles

### **🗑️ `clean_tables.sql`**
**Usage :** `psql -d OST_PROD -f scripts/database/clean_tables.sql`

**Description :** Nettoie toutes les tables opérationnelles en préservant les tables de référence (`CATEGORY`, `TECH_STACK`).

**Tables nettoyées :**
- `github_PROJECT`, `USER`, `PROJECT`
- `USER_CATEGORY`, `USER_TECH_STACK`
- `PROJECT_CATEGORY`, `PROJECT_TECH_STACK`
- `embed_PROJECTS`, `embed_USERS`
- Et toutes les autres tables opérationnelles

### **👥 `create_test_users.py`**
**Usage :** `python scripts/database/create_test_users.py`

**Description :** Crée 10 utilisateurs de test avec des profils réalistes et les mappe automatiquement aux catégories et tech stacks.

**Utilisateurs créés :**
- `alice_ml` - Senior ML Engineer
- `bob_webdev` - Full-stack web developer
- `carol_devops` - DevOps engineer
- `dave_security` - Cybersecurity expert
- `eve_data` - Senior Data Scientist
- `frank_mobile` - Mobile app developer
- `grace_blockchain` - Blockchain developer
- `henry_opensource` - Open source maintainer
- `iris_education` - Tech educator
- `jack_gaming` - Game developer

### **🏗️ `recreate_schema.sql`**
**Usage :** `psql -d OST_PROD -f scripts/database/recreate_schema.sql`

**Description :** Script SQL complet pour recréer tout le schéma de base de données.

**Inclut :**
- Toutes les tables principales
- Tables de référence (`CATEGORY`, `TECH_STACK`)
- Tables de relations
- Tables ML (`embed_PROJECTS`, `embed_USERS`, etc.)
- Index de performance
- Données de référence par défaut

### **🐍 `recreate_schema.py`**
**Usage :** `python scripts/database/recreate_schema.py`

**Description :** Script Python pour recréer le schéma via SQLAlchemy.

**Avantages :**
- Utilise les modèles SQLAlchemy
- Validation automatique
- Gestion des erreurs
- Confirmation pour les environnements de production

## 🔄 Workflow typique

### **1. Reset complet de la base**
```bash
# Option 1: Via SQL (plus rapide)
psql -d OST_PROD -f scripts/database/recreate_schema.sql

# Option 2: Via Python (plus sûr)
python scripts/database/recreate_schema.py
```

### **2. Nettoyer les données**
```bash
psql -d OST_PROD -f scripts/database/clean_tables.sql
```

### **3. Créer des données de test**
```bash
python scripts/database/create_test_users.py
```

### **4. Lancer le pipeline Dagster**
```bash
export DAGSTER_HOME=$(pwd)/logs/dagster
poetry run dagster asset materialize -m src.infrastructure.pipeline.dagster.definitions --select training_data_pipeline
```

## ⚠️ Notes importantes

- **Sauvegarde** : Toujours faire une sauvegarde avant de recréer le schéma
- **Production** : Le script Python demande confirmation en production
- **Dépendances** : Les scripts Python nécessitent les dépendances du projet
- **Variables d'environnement** : Assurez-vous que `.env` est configuré

## 🗑️ Scripts supprimés

Les scripts suivants ont été supprimés car leurs fonctionnalités sont maintenant intégrées dans le pipeline Dagster :

- `test_user_recommendations.py` → Remplacé par `test_single_user_evaluation.py`
- `test_user_project_similarity.py` → Intégré dans le pipeline Dagster
- `create_user_category_table.sql` → Inclus dans `recreate_schema.sql`
- `map_projects_to_references.py` → Intégré dans `reference_assets.py`
- `populate_reference_tables.py` → Intégré dans `reference_assets.py`
