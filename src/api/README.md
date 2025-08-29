# API de Recommandations - Architecture

## 🏗️ Architecture

### **Pipeline ML (Python/Dagster)**
1. **Embeddings** : Génère les embeddings sémantiques et hybrides
2. **Similarités** : Calcule et stocke les similarités User↔Project
3. **Stockage** : PostgreSQL avec pgvector + table `USER_PROJECT_SIMILARITY`

### **API Go**
- **Endpoint** : `/recommendations?user_id=<uuid>`
- **Source** : Table `USER_PROJECT_SIMILARITY` pré-calculée
- **Performance** : Requêtes SQL optimisées avec index

### **Cache Redis** (optionnel)
- **Clé** : `user_recommendations:{user_id}`
- **TTL** : 1 heure
- **Valeur** : Top-N recommandations JSON

## 📊 Variables d'Environnement

```env
# Configuration des recommandations
RECOMMENDATION_TOP_N=5                    # Nombre de recommandations retournées
RECOMMENDATION_MIN_SIMILARITY=0.1         # Seuil minimum de similarité
RECOMMENDATION_SEMANTIC_WEIGHT=0.25       # Poids sémantique
RECOMMENDATION_CATEGORY_WEIGHT=0.45       # Poids catégories
RECOMMENDATION_TECH_WEIGHT=0.5            # Poids tech stacks
RECOMMENDATION_POPULARITY_WEIGHT=0.1      # Poids popularité

# Configuration API
GO_API_PORT=8080                          # Port de l'API Go
DATABASE_URL=postgresql://...             # URL PostgreSQL
CACHE_ENABLED=true                        # Activer le cache Redis
CACHE_TTL=3600                           # TTL du cache (secondes)
```

## 🔄 Workflow

### **1. Pipeline Dagster**
```bash
# Calculer toutes les similarités
dagster asset materialize --select user_project_similarities
```

### **2. API Go**
```bash
# Démarrer l'API
go run src/api/go/recommendations.go
```

### **3. Requête API**
```bash
curl "http://localhost:8080/recommendations?user_id=9759b805-6201-4648-bf13-3aa594a791d2"
```

## 📈 Performance

### **Calcul des Similarités**
- **10 utilisateurs × 979 projets = 9,790 calculs**
- **Temps estimé** : ~30-60 secondes
- **Stockage** : ~100KB de données

### **API Go**
- **Latence** : <10ms (requête SQL directe)
- **Throughput** : 1000+ req/s
- **Cache** : <1ms (Redis)

## 🗄️ Structure de Données

### **Table USER_PROJECT_SIMILARITY**
```sql
CREATE TABLE "USER_PROJECT_SIMILARITY" (
    user_id UUID REFERENCES "USER"(id),
    project_id UUID REFERENCES "PROJECT"(id),
    similarity_score FLOAT NOT NULL,           -- Score combiné (0-1)
    semantic_similarity FLOAT,                 -- Similarité sémantique
    category_similarity FLOAT,                 -- Overlap catégories
    tech_similarity FLOAT,                     -- Overlap tech stacks
    popularity_score FLOAT,                    -- Score popularité
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);
```

### **Index de Performance**
```sql
CREATE INDEX idx_user_project_similarity_score ON "USER_PROJECT_SIMILARITY" (user_id, similarity_score);
```

## 🎯 Avantages

1. **Performance** : Similarités pré-calculées
2. **Scalabilité** : API Go + PostgreSQL
3. **Flexibilité** : Paramètres configurables
4. **Traçabilité** : Scores détaillés
5. **Cache** : Redis pour performance

## 🚀 Déploiement

### **1. Pipeline ML**
```bash
# Exécuter le pipeline complet
dagster job execute -f src/infrastructure/pipeline/dagster/definitions.py -j training_data_pipeline
```

### **2. API Go**
```bash
# Compiler et déployer
go build -o recommendations-api src/api/go/recommendations.go
./recommendations-api
```

### **3. Cache Redis** (optionnel)
```bash
# Démarrer Redis
redis-server --port 6380
```
