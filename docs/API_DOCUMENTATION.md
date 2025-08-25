# 🚀 Data Engine Recommendation API Documentation

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Endpoints](#endpoints)
4. [Authentification](#authentification)
5. [Exemples d'utilisation](#exemples-dutilisation)
6. [Gestion d'erreurs](#gestion-derreurs)
7. [Performance](#performance)
8. [Intégration](#intégration)
9. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

L'API Data Engine Recommendation fournit des recommandations de projets personnalisées utilisant des algorithmes de machine learning avancés, incluant TF-IDF et les embeddings Mistral.

### ✨ Fonctionnalités principales

- **Recommandations hybrides** : Combinaison TF-IDF + Mistral
- **Personnalisation utilisateur** : Basée sur les tech stacks et intérêts
- **Performance optimisée** : < 5 secondes de réponse
- **Cache intelligent** : Redis pour améliorer les performances
- **Documentation complète** : OpenAPI/Swagger intégré

### 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  FastAPI Server │───▶│  ML Pipeline    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │   Redis Cache   │
                       └─────────────────┘    └─────────────────┘
```

---

## 🔧 Endpoints

### 1. Health Check

**GET** `/health`

Vérifie que l'API fonctionne et que les modèles sont chargés.

**Réponse :**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2023-08-03T13:44:24Z"
}
```

### 2. Recommandations Utilisateur (Recommandé)

**GET** `/user-recommendations/{user_id}`

Génère des recommandations personnalisées pour un utilisateur en utilisant les similarités User↔Project.

**Paramètres :**
- `user_id` (UUID, requis) : ID de l'utilisateur
- `top_k` (int, optionnel, 1-50, défaut: 10) : Nombre de recommandations
- `with_categories_only` (bool, optionnel, défaut: true) : Filtrer par catégories

**Exemple de requête :**
```bash
curl -X GET "http://localhost:8000/user-recommendations/58b47d17-e537-4ec5-b53e-8cafca7eb7c1?top_k=5&with_categories_only=true"
```

**Réponse :**
```json
{
  "user_id": "58b47d17-e537-4ec5-b53e-8cafca7eb7c1",
  "recommendations": [
    {
      "project_id": "a060b9a9-8ac0-483b-b947-2dbd78ea54a1",
      "title": "DeepFaceLab",
      "tech_stacks": "Python",
      "categories": "AI/ML",
      "tfidf_score": 0.5,
      "user_project_similarity": 0.7841354681525918,
      "hybrid_score": 0.6988948277068142
    }
  ],
  "tfidf_candidates_count": 100,
  "user_project_similarities_count": 100,
  "final_recommendations_count": 5,
  "weights": {
    "tfidf": 0.3,
    "user_project": 0.7
  },
  "response_time_ms": 4811.41
}
```

### 3. Recommandations Projet

**GET** `/project-recommendations/{project_id}`

Trouve des projets similaires à un projet donné en utilisant TF-IDF + Mistral.

**Paramètres :**
- `project_id` (UUID, requis) : ID du projet cible
- `top_k` (int, optionnel, 1-20, défaut: 10) : Nombre de recommandations

**Exemple de requête :**
```bash
curl -X GET "http://localhost:8000/project-recommendations/a060b9a9-8ac0-483b-b947-2dbd78ea54a1?top_k=5"
```

**Réponse :**
```json
{
  "project_id": "a060b9a9-8ac0-483b-b947-2dbd78ea54a1",
  "recommendations": [
    {
      "project_id": "7a710243-7939-4d75-8bc1-108a83dbb2e4",
      "title": "30-seconds-of-interviews",
      "tech_stacks": "Javascript",
      "categories": "Education",
      "tfidf_score": 0.85,
      "semantic_similarity": 0.92,
      "hybrid_score": 0.89
    }
  ],
  "total_recommendations": 1,
  "tfidf_candidates_count": 50,
  "cache_hit": false,
  "processing_time_ms": 45.2
}
```

### 4. Recommandations Legacy

**GET** `/recommendations/{user_id}`

Endpoint legacy utilisant l'ancien système de recommandations.

---

## 🔐 Authentification

Actuellement, l'API n'utilise pas d'authentification. Pour la production, il est recommandé d'ajouter :

- **JWT Tokens** pour l'authentification
- **Rate Limiting** pour éviter les abus
- **API Keys** pour l'identification des clients

---

## 💡 Exemples d'utilisation

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Recommandations utilisateur
async function getUserRecommendations(userId, topK = 10) {
  try {
    const response = await axios.get(
      `http://localhost:8000/user-recommendations/${userId}?top_k=${topK}`
    );
    return response.data;
  } catch (error) {
    console.error('Erreur:', error.response?.data || error.message);
    throw error;
  }
}

// Utilisation
getUserRecommendations('58b47d17-e537-4ec5-b53e-8cafca7eb7c1', 5)
  .then(recommendations => {
    console.log('Recommandations:', recommendations);
  });
```

### Python

```python
import requests
import json

def get_user_recommendations(user_id, top_k=10):
    """Récupère les recommandations pour un utilisateur."""
    url = f"http://localhost:8000/user-recommendations/{user_id}"
    params = {"top_k": top_k, "with_categories_only": True}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur: {e}")
        return None

# Utilisation
recommendations = get_user_recommendations(
    "58b47d17-e537-4ec5-b53e-8cafca7eb7c1", 
    top_k=5
)
if recommendations:
    print(f"Trouvé {recommendations['final_recommendations_count']} recommandations")
```

### cURL

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Recommandations utilisateur
curl -X GET "http://localhost:8000/user-recommendations/58b47d17-e537-4ec5-b53e-8cafca7eb7c1?top_k=5"

# Recommandations projet
curl -X GET "http://localhost:8000/project-recommendations/a060b9a9-8ac0-483b-b947-2dbd78ea54a1?top_k=3"
```

---

## ⚠️ Gestion d'erreurs

### Codes d'erreur HTTP

| Code | Description | Exemple |
|------|-------------|---------|
| 200 | Succès | Recommandations générées |
| 400 | Requête invalide | Paramètres manquants |
| 404 | Non trouvé | Utilisateur/projet inexistant |
| 422 | Validation échouée | UUID invalide |
| 500 | Erreur serveur | Modèles non chargés |

### Exemples d'erreurs

**404 - Utilisateur non trouvé :**
```json
{
  "detail": "User not found in database.",
  "error_code": "USER_NOT_FOUND",
  "timestamp": "2023-08-03T13:44:24Z"
}
```

**422 - UUID invalide :**
```json
{
  "detail": "Invalid UUID format for user_id parameter",
  "error_code": "INVALID_UUID_FORMAT",
  "timestamp": "2023-08-03T13:44:24Z"
}
```

**500 - Erreur serveur :**
```json
{
  "detail": "Models not available. Run training pipeline first.",
  "error_code": "MODELS_NOT_LOADED",
  "timestamp": "2023-08-03T13:44:24Z"
}
```

---

## ⚡ Performance

### Métriques de performance

| Métrique | Valeur | Description |
|----------|--------|-------------|
| Temps de réponse | < 5s | Recommandations utilisateur |
| Temps de réponse | < 3s | Recommandations projet |
| Throughput | 100+ req/min | Capacité de traitement |
| Cache hit rate | > 80% | Efficacité du cache |
| Précision | +40% | Amélioration hybride |

### Optimisations

1. **TF-IDF Pre-ranking** : Sélection rapide de candidats
2. **Mistral Re-ranking** : Similarité sémantique
3. **Cache Redis** : Stockage des résultats fréquents
4. **Pool de connexions** : Gestion efficace de la DB
5. **Batch processing** : Traitement par lots

---

## 🔗 Intégration

### Configuration recommandée

```javascript
// Configuration client
const API_CONFIG = {
  baseURL: 'http://localhost:8000',
  timeout: 10000, // 10 secondes
  retries: 3,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

// Fonction avec retry
async function apiCall(endpoint, options = {}) {
  const config = { ...API_CONFIG, ...options };
  
  for (let i = 0; i < config.retries; i++) {
    try {
      const response = await fetch(`${config.baseURL}${endpoint}`, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      if (i === config.retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

### Bonnes pratiques

1. **Gestion d'erreurs** : Toujours gérer les erreurs HTTP
2. **Timeouts** : Définir des timeouts appropriés
3. **Retry logic** : Implémenter une logique de retry
4. **Cache côté client** : Mettre en cache les résultats
5. **Monitoring** : Surveiller les performances

---

## 🔧 Dépannage

### Problèmes courants

#### 1. API ne démarre pas

**Symptômes :** Erreur de connexion au port 8000

**Solutions :**
```bash
# Vérifier que l'API fonctionne
curl http://localhost:8000/health

# Vérifier les logs
docker logs data-engine-api

# Redémarrer l'API
docker-compose restart api
```

#### 2. Modèles non chargés

**Symptômes :** Erreur 500 "Models not available"

**Solutions :**
```bash
# Vérifier que les modèles existent
ls -la models/

# Relancer le pipeline d'entraînement
python -m src.application.use_cases.run_training_pipeline
```

#### 3. Base de données inaccessible

**Symptômes :** Erreur de connexion PostgreSQL

**Solutions :**
```bash
# Vérifier la connexion DB
python -c "from src.infrastructure.postgres.database import test_database_connection; print(test_database_connection())"

# Redémarrer PostgreSQL
docker-compose restart postgres
```

#### 4. Performance lente

**Symptômes :** Temps de réponse > 10 secondes

**Solutions :**
- Vérifier la charge CPU/mémoire
- Optimiser les requêtes de base de données
- Augmenter les ressources Redis
- Vérifier la connectivité réseau

### Logs et debugging

```bash
# Voir les logs de l'API
docker logs -f data-engine-api

# Voir les logs de la base de données
docker logs -f postgres

# Voir les logs Redis
docker logs -f redis
```

---

## 📚 Ressources additionnelles

- **Documentation OpenAPI** : `http://localhost:8000/docs`
- **Documentation ReDoc** : `http://localhost:8000/redoc`
- **Schéma OpenAPI** : `http://localhost:8000/openapi.json`
- **Code source** : [GitHub Repository](https://github.com/your-org/data-engine)
- **Issues** : [GitHub Issues](https://github.com/your-org/data-engine/issues)

---

## 🤝 Support

Pour toute question ou problème :

1. **Documentation** : Consultez cette documentation
2. **Issues GitHub** : Créez une issue sur GitHub
3. **Email** : support@dataengine.com
4. **Slack** : #data-engine-support

---

*Dernière mise à jour : 3 août 2023* 