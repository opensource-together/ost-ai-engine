# 📊 Modèle Conceptuel de Données (MCD) — Open Source Together

## 🎯 Vue d'ensemble

Ce document présente le Modèle Conceptuel de Données (MCD) d'OST, aligné sur le schema de production Prisma. Il décrit les entités, leurs attributs et les relations entre elles.

---

## 🏗️ Entités Principales

### **User** — Utilisateur
```
User {
  id: UUID (PK)
  username: String(30) UNIQUE NOT NULL
  email: String(255) UNIQUE NOT NULL
  login: String(100) // GitHub login
  avatar_url: Text // GitHub avatar URL
  location: String(100)
  company: String(100)
  bio: Text
  created_at: DateTime
  updated_at: DateTime
}
```

### **Project** — Projet
```
Project {
  id: UUID (PK)
  author_id: UUID (FK → User)
  title: String(100) NOT NULL
  description: Text
  short_description: Text
  image: Text // URL de l'image
  cover_images: Text // JSON array d'URLs
  readme: Text // Contenu README GitHub
  created_at: DateTime
  updated_at: DateTime
}
```

### **TechStack** — Technologies
```
TechStack {
  id: UUID (PK)
  name: String(100) UNIQUE NOT NULL
  icon_url: Text
  type: String(20) // "LANGUAGE" ou "TECH"
  created_at: DateTime
}
```

### **Category** — Catégories
```
Category {
  id: UUID (PK)
  name: String(100) UNIQUE NOT NULL
  created_at: DateTime
}
```

### **ProjectRole** — Rôle de Projet
```
ProjectRole {
  id: UUID (PK)
  project_id: UUID (FK → Project) NOT NULL
  title: String(100) NOT NULL
  description: Text
  is_filled: Boolean DEFAULT FALSE
  created_at: DateTime
  updated_at: DateTime
}
```

### **TeamMember** — Membre d'Équipe
```
TeamMember {
  id: UUID (PK)
  user_id: UUID (FK → User) NOT NULL
  project_id: UUID (FK → Project) NOT NULL
  joined_at: DateTime
}
```

---

## 🔗 Entités de Support

### **UserGitHubCredentials** — Credentials GitHub
```
UserGitHubCredentials {
  user_id: UUID (PK, FK → User)
  github_access_token: Text
  github_user_id: String(100)
  created_at: DateTime
  updated_at: DateTime
}
```

### **ProjectExternalLink** — Liens Externes
```
ProjectExternalLink {
  id: UUID (PK)
  project_id: UUID (FK → Project) NOT NULL
  type: String(50) // "github", "website", "documentation"
  url: Text NOT NULL
}
```

### **KeyFeature** — Fonctionnalités Clés
```
KeyFeature {
  id: UUID (PK)
  project_id: UUID (FK → Project) NOT NULL
  feature: String(200) NOT NULL
}
```

### **ProjectGoal** — Objectifs de Projet
```
ProjectGoal {
  id: UUID (PK)
  project_id: UUID (FK → Project) NOT NULL
  goal: String(200) NOT NULL
}
```

### **UserSocialLink** — Liens Sociaux
```
UserSocialLink {
  id: UUID (PK)
  user_id: UUID (FK → User) NOT NULL
  type: String(50) // "github", "twitter", "linkedin"
  url: Text NOT NULL
  created_at: DateTime
}
```

---

## 🎯 Entités de Candidature

### **ProjectRoleApplication** — Candidature
```
ProjectRoleApplication {
  id: UUID (PK)
  project_id: UUID (FK → Project) NOT NULL
  project_title: String(100) // Historique
  project_role_id: UUID (FK → ProjectRole) NOT NULL
  project_role_title: String(100) // Historique
  project_description: Text
  status: String(20) // "pending", "accepted", "rejected", "withdrawn"
  motivation_letter: Text
  rejection_reason: Text
  applied_at: DateTime
  created_at: DateTime
  updated_at: DateTime
}
```

---

## 🔗 Relations

### **Relations One-to-Many**

1. **User → Project** (1:N)
   - Un utilisateur peut créer plusieurs projets
   - Un projet appartient à un seul utilisateur (auteur)

2. **User → TeamMember** (1:N)
   - Un utilisateur peut être membre de plusieurs équipes
   - Un membre d'équipe appartient à un seul utilisateur

3. **User → ProjectRoleApplication** (1:N)
   - Un utilisateur peut avoir plusieurs candidatures
   - Une candidature appartient à un seul utilisateur

4. **User → UserSocialLink** (1:N)
   - Un utilisateur peut avoir plusieurs liens sociaux
   - Un lien social appartient à un seul utilisateur

5. **Project → ProjectRole** (1:N)
   - Un projet peut avoir plusieurs rôles
   - Un rôle appartient à un seul projet

6. **Project → TeamMember** (1:N)
   - Un projet peut avoir plusieurs membres
   - Un membre appartient à un seul projet

7. **Project → ProjectExternalLink** (1:N)
   - Un projet peut avoir plusieurs liens externes
   - Un lien externe appartient à un seul projet

8. **Project → KeyFeature** (1:N)
   - Un projet peut avoir plusieurs fonctionnalités clés
   - Une fonctionnalité appartient à un seul projet

9. **Project → ProjectGoal** (1:N)
   - Un projet peut avoir plusieurs objectifs
   - Un objectif appartient à un seul projet

10. **Project → ProjectRoleApplication** (1:N)
    - Un projet peut avoir plusieurs candidatures
    - Une candidature appartient à un seul projet

11. **ProjectRole → ProjectRoleApplication** (1:N)
    - Un rôle peut avoir plusieurs candidatures
    - Une candidature appartient à un seul rôle

### **Relations One-to-One**

1. **User ↔ UserGitHubCredentials** (1:1)
   - Un utilisateur a au plus un set de credentials GitHub
   - Un set de credentials appartient à un seul utilisateur

### **Relations Many-to-Many**

1. **User ↔ TechStack** (N:N) via `UserTechStack`
   - Un utilisateur peut maîtriser plusieurs technologies
   - Une technologie peut être maîtrisée par plusieurs utilisateurs

2. **Project ↔ TechStack** (N:N) via `ProjectTechStack`
   - Un projet peut utiliser plusieurs technologies
   - Une technologie peut être utilisée par plusieurs projets

3. **Project ↔ Category** (N:N) via `ProjectCategory`
   - Un projet peut appartenir à plusieurs catégories
   - Une catégorie peut contenir plusieurs projets

4. **ProjectRole ↔ TechStack** (N:N) via `ProjectRoleTechStack`
   - Un rôle peut nécessiter plusieurs technologies
   - Une technologie peut être requise par plusieurs rôles

5. **TeamMember ↔ ProjectRole** (N:N) via `TeamMemberProjectRole`
   - Un membre peut occuper plusieurs rôles
   - Un rôle peut être occupé par plusieurs membres

6. **ProjectRoleApplication ↔ KeyFeature** (N:N) via `ProjectRoleApplicationKeyFeature`
   - Une candidature peut sélectionner plusieurs fonctionnalités
   - Une fonctionnalité peut être sélectionnée par plusieurs candidatures

7. **ProjectRoleApplication ↔ ProjectGoal** (N:N) via `ProjectRoleApplicationProjectGoal`
   - Une candidature peut sélectionner plusieurs objectifs
   - Un objectif peut être sélectionné par plusieurs candidatures

---

## 📊 Contraintes d'Intégrité

### **Contraintes Métier**

1. **Unicité des membres** : Un utilisateur ne peut être membre que d'une fois par projet
2. **Cohérence des candidatures** : Une candidature ne peut être liée qu'à un rôle d'un projet
3. **Historique des applications** : Les champs `project_title` et `project_role_title` sont conservés pour l'historique
4. **Statuts cohérents** : Les statuts des candidatures suivent un workflow défini

### **Contraintes Techniques**

1. **Clés étrangères** : Toutes les FK sont correctement définies avec CASCADE où approprié
2. **Unicité** : Les contraintes UNIQUE sont respectées (username, email, etc.)
3. **Timestamps** : `created_at` et `updated_at` sont automatiquement gérés
4. **UUIDs** : Toutes les clés primaires utilisent UUID pour la scalabilité

---

## 🎯 Alignement avec la Production

Cette conception est **100% alignée** avec le schema Prisma de production :

### **✅ Correspondances Directes**
- `User` ↔ `User` (prod)
- `Project` ↔ `Project` (prod) 
- `TechStack` ↔ `TechStack` (prod)
- `Category` ↔ `Category` (prod)
- `ProjectRole` ↔ `ProjectRole` (prod)
- `TeamMember` ↔ `teamMember` (prod)
- `ProjectRoleApplication` ↔ `ProjectRoleApplication` (prod)

### **✅ Champs Spécifiques**
- `readme` : Présent dans `Project` (prod)
- `cover_images` : Array d'URLs (prod)
- `short_description` : Description courte (prod)
- `external_links` : Liens externes via `ProjectExternalLink` (prod)

### **✅ Relations Many-to-Many**
- Utilisation de tables d'association (comme en prod)
- Pas de champs JSON pour les relations complexes
- Structure relationnelle pure

---

## 🚀 Avantages de cette Architecture

### **1. Cohérence Production**
- Schema identique entre dev et prod
- Pas de divergence de structure
- Migration facilitée

### **2. Scalabilité**
- UUIDs pour les clés primaires
- Index optimisés sur les colonnes de recherche
- Structure normalisée

### **3. Flexibilité**
- Relations many-to-many extensibles
- Support des métadonnées (timestamps, statuts)
- Historique des changements

### **4. Performance**
- Requêtes optimisées avec les bonnes relations
- Index sur les colonnes fréquemment utilisées
- Structure adaptée aux patterns d'usage

---

## 📝 Notes d'Implémentation

### **Pour le ML**
- Le champ `readme` est disponible pour TF-IDF
- Les relations `ProjectTechStack` permettent l'analyse des technologies
- Les `ProjectRoleApplication` fournissent des données d'entraînement

### **Pour l'API**
- Structure optimisée pour les requêtes REST
- Relations claires pour les endpoints
- Support des filtres et de la pagination

### **Pour la Maintenance**
- Schema documenté et cohérent
- Migrations simplifiées
- Tests facilités par la structure claire
