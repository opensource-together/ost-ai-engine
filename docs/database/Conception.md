# 📘 Conception de la Base de Données — Open Source Together

## 🎯 Vue d'ensemble

Cette documentation décrit la conception de la base de données d'OST, alignée sur le schema de production Prisma. L'architecture suit les principes de conception relationnelle avec des entités clairement définies et des relations many-to-many gérées via des tables d'association.

## 🏗️ Architecture Générale

### **Entités Principales**
- **User** : Utilisateurs de la plateforme
- **Project** : Projets open source
- **TechStack** : Technologies et outils (unifiés)
- **Category** : Catégories de projets
- **ProjectRole** : Rôles dans les projets
- **TeamMember** : Membres d'équipe

### **Entités de Support**
- **UserGitHubCredentials** : Credentials GitHub
- **ProjectExternalLink** : Liens externes des projets
- **KeyFeature** : Fonctionnalités clés des projets
- **ProjectGoal** : Objectifs des projets
- **UserSocialLink** : Liens sociaux des utilisateurs

### **Tables d'Association**
- **ProjectTechStack** : Projets ↔ Technologies
- **UserTechStack** : Utilisateurs ↔ Technologies
- **ProjectCategory** : Projets ↔ Catégories
- **ProjectRoleTechStack** : Rôles ↔ Technologies
- **TeamMemberProjectRole** : Membres ↔ Rôles
- **ProjectRoleApplicationKeyFeature** : Applications ↔ Fonctionnalités
- **ProjectRoleApplicationProjectGoal** : Applications ↔ Objectifs

## 📊 Modèle Conceptuel de Données (MCD)

### **User (Utilisateur)**
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

**Relations :**
- `User` → `UserGitHubCredentials` (1:1)
- `User` → `Project` (1:N) // Projets créés
- `User` → `TeamMember` (1:N) // Appartenance aux équipes
- `User` → `ProjectRoleApplication` (1:N) // Candidatures
- `User` → `UserSocialLink` (1:N) // Liens sociaux
- `User` ↔ `TechStack` (N:N) via `UserTechStack`

### **Project (Projet)**
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

**Relations :**
- `Project` → `User` (N:1) // Auteur
- `Project` → `ProjectExternalLink` (1:N) // Liens externes
- `Project` → `ProjectRole` (1:N) // Rôles disponibles
- `Project` → `TeamMember` (1:N) // Membres d'équipe
- `Project` → `KeyFeature` (1:N) // Fonctionnalités
- `Project` → `ProjectGoal` (1:N) // Objectifs
- `Project` → `ProjectRoleApplication` (1:N) // Candidatures
- `Project` ↔ `TechStack` (N:N) via `ProjectTechStack`
- `Project` ↔ `Category` (N:N) via `ProjectCategory`

### **TechStack (Technologies)**
```
TechStack {
  id: UUID (PK)
  name: String(100) UNIQUE NOT NULL
  icon_url: Text
  type: String(20) // "LANGUAGE" ou "TECH"
  created_at: DateTime
}
```

**Relations :**
- `TechStack` ↔ `User` (N:N) via `UserTechStack`
- `TechStack` ↔ `Project` (N:N) via `ProjectTechStack`
- `TechStack` ↔ `ProjectRole` (N:N) via `ProjectRoleTechStack`

### **ProjectRole (Rôle de Projet)**
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

**Relations :**
- `ProjectRole` → `Project` (N:1)
- `ProjectRole` → `ProjectRoleApplication` (1:N) // Candidatures
- `ProjectRole` ↔ `TechStack` (N:N) via `ProjectRoleTechStack`
- `ProjectRole` ↔ `TeamMember` (N:N) via `TeamMemberProjectRole`

### **TeamMember (Membre d'Équipe)**
```
TeamMember {
  id: UUID (PK)
  user_id: UUID (FK → User) NOT NULL
  project_id: UUID (FK → Project) NOT NULL
  joined_at: DateTime
}
```

**Relations :**
- `TeamMember` → `User` (N:1)
- `TeamMember` → `Project` (N:1)
- `TeamMember` ↔ `ProjectRole` (N:N) via `TeamMemberProjectRole`

### **ProjectRoleApplication (Candidature)**
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

**Relations :**
- `ProjectRoleApplication` → `Project` (N:1)
- `ProjectRoleApplication` → `ProjectRole` (N:1)
- `ProjectRoleApplication` → `User` (N:1)
- `ProjectRoleApplication` ↔ `KeyFeature` (N:N) via `ProjectRoleApplicationKeyFeature`
- `ProjectRoleApplication` ↔ `ProjectGoal` (N:N) via `ProjectRoleApplicationProjectGoal`

## 🔗 Tables d'Association

### **ProjectTechStack**
```sql
CREATE TABLE "PROJECT_TECH_STACK" (
  project_id UUID REFERENCES "PROJECT"(id),
  tech_stack_id UUID REFERENCES "TECH_STACK"(id),
  PRIMARY KEY (project_id, tech_stack_id)
);
```

### **UserTechStack**
```sql
CREATE TABLE "USER_TECH_STACK" (
  user_id UUID REFERENCES "USER"(id),
  tech_stack_id UUID REFERENCES "TECH_STACK"(id),
  PRIMARY KEY (user_id, tech_stack_id)
);
```

### **ProjectCategory**
```sql
CREATE TABLE "PROJECT_CATEGORY" (
  project_id UUID REFERENCES "PROJECT"(id),
  category_id UUID REFERENCES "CATEGORY"(id),
  PRIMARY KEY (project_id, category_id)
);
```

## 📋 Contraintes d'Intégrité

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
