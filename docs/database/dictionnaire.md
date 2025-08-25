# 📘 Dictionnaire de Données — Open Source Together

## 🎯 Vue d'ensemble

Ce dictionnaire décrit la structure complète de la base de données d'OST, alignée sur le schema de production Prisma. Chaque entité est documentée avec ses champs, contraintes et relations.

---

## 🏗️ Entités Principales

### **User** — Utilisateur

| Nom         | Type       | Description                    | Valeurs possibles                      | Contraintes                  | Priorité |
| ----------- | ---------- | ------------------------------ | -------------------------------------- | ---------------------------- | -------- |
| id          | UUID       | Identifiant unique utilisateur | UUID                                   | PK, unique                   | MVP      |
| username    | String(30) | Nom d'utilisateur affiché      | Max 30 caractères                      | Obligatoire, unique          | MVP      |
| email       | String(255)| Adresse email                  | Format email                           | Obligatoire, unique          | MVP      |
| login       | String(100)| GitHub login                   | Nom d'utilisateur GitHub               | Optionnel                    | MVP      |
| avatar_url  | Text       | GitHub avatar URL              | URL de l'avatar GitHub                 | Optionnel                    | MVP      |
| location    | String(100)| Localisation géographique      | Max 100 caractères                     | Optionnel                    | MVP      |
| company     | String(100)| Nom de l'entreprise            | Max 100 caractères                     | Optionnel                    | MVP      |
| bio         | Text       | Bio de l'utilisateur           | Max 500 caractères                     | Optionnel                    | MVP      |
| created_at  | DateTime   | Date de création du compte     | ISO 8601                               | Automatique                  | MVP      |
| updated_at  | DateTime   | Dernière mise à jour           | ISO 8601                               | Automatique                  | MVP      |

**Relations :**
- `User` → `UserGitHubCredentials` (1:1)
- `User` → `Project` (1:N) // Projets créés
- `User` → `TeamMember` (1:N) // Appartenance aux équipes
- `User` → `ProjectRoleApplication` (1:N) // Candidatures
- `User` → `UserSocialLink` (1:N) // Liens sociaux
- `User` ↔ `TechStack` (N:N) via `UserTechStack`

### **Project** — Projet

| Nom                 | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ------------------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id                  | UUID       | Identifiant du projet          | UUID                                   | PK, unique                | MVP      |
| author_id           | UUID       | Auteur du projet               | Référence User                         | FK vers User              | MVP      |
| title               | String(100)| Titre du projet                | Max 100 caractères                     | Obligatoire               | MVP      |
| description         | Text       | Description complète du projet | Max 2000 caractères                   | Optionnel                 | MVP      |
| short_description   | Text       | Description courte             | Max 500 caractères                    | Optionnel                 | MVP      |
| image               | Text       | URL de l'image du projet       | URL de l'image                         | Optionnel                 | MVP      |
| cover_images        | Text       | Array d'URLs d'images          | JSON array d'URLs (1-4 images)        | Optionnel                 | MVP      |
| readme              | Text       | Contenu README GitHub          | Contenu du README.md                   | Optionnel                 | MVP      |
| created_at          | DateTime   | Date de création               | ISO 8601                               | Automatique               | MVP      |
| updated_at          | DateTime   | Dernière mise à jour           | ISO 8601                               | Automatique               | MVP      |

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

### **TechStack** — Technologies

| Nom         | Type       | Description                    | Valeurs possibles                      | Contraintes         | Priorité |
| ----------- | ---------- | ------------------------------ | -------------------------------------- | ------------------- | -------- |
| id          | UUID       | Identifiant de la technologie  | UUID                                   | PK, unique          | MVP      |
| name        | String(100)| Nom de la technologie          | "React", "Python", "Docker", etc.      | Obligatoire, unique | MVP      |
| icon_url    | Text       | URL de l'icône                 | URL de l'icône                         | Optionnel           | MVP      |
| type        | String(20) | Type de technologie            | "LANGUAGE" ou "TECH"                   | Enum                | MVP      |
| created_at  | DateTime   | Date de création               | ISO 8601                               | Automatique         | MVP      |

**Relations :**
- `TechStack` ↔ `User` (N:N) via `UserTechStack`
- `TechStack` ↔ `Project` (N:N) via `ProjectTechStack`
- `TechStack` ↔ `ProjectRole` (N:N) via `ProjectRoleTechStack`

### **Category** — Catégories

| Nom         | Type       | Description                    | Valeurs possibles                      | Contraintes         | Priorité |
| ----------- | ---------- | ------------------------------ | -------------------------------------- | ------------------- | -------- |
| id          | UUID       | Identifiant de la catégorie    | UUID                                   | PK, unique          | MVP      |
| name        | String(100)| Nom de la catégorie            | "Education", "Finance", "Gaming", etc. | Obligatoire, unique | MVP      |
| created_at  | DateTime   | Date de création               | ISO 8601                               | Automatique         | MVP      |

**Relations :**
- `Category` ↔ `Project` (N:N) via `ProjectCategory`

### **ProjectRole** — Rôle de Projet

| Nom         | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ----------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id          | UUID       | Identifiant du rôle            | UUID                                   | PK, unique                | MVP      |
| project_id  | UUID       | Projet concerné                | Référence Project                      | FK vers Project, obligatoire | MVP   |
| title       | String(100)| Titre du rôle                  | "Frontend Lead", "UX Designer", etc.   | Obligatoire               | MVP      |
| description | Text       | Description du rôle            | Max 1000 caractères                   | Optionnel                 | MVP      |
| is_filled   | Boolean    | Rôle pourvu ou non             | true/false                             | Défaut: false             | MVP      |
| created_at  | DateTime   | Date de création               | ISO 8601                               | Automatique               | MVP      |
| updated_at  | DateTime   | Dernière mise à jour           | ISO 8601                               | Automatique               | MVP      |

**Relations :**
- `ProjectRole` → `Project` (N:1)
- `ProjectRole` → `ProjectRoleApplication` (1:N) // Candidatures
- `ProjectRole` ↔ `TechStack` (N:N) via `ProjectRoleTechStack`
- `ProjectRole` ↔ `TeamMember` (N:N) via `TeamMemberProjectRole`

### **TeamMember** — Membre d'Équipe

| Nom         | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ----------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id          | UUID       | Identifiant du membre          | UUID                                   | PK, unique                | MVP      |
| user_id     | UUID       | Utilisateur membre             | Référence User                         | FK vers User, obligatoire  | MVP      |
| project_id  | UUID       | Projet concerné                | Référence Project                      | FK vers Project, obligatoire | MVP   |
| joined_at   | DateTime   | Date d'entrée dans l'équipe    | ISO 8601                               | Automatique               | MVP      |

**Relations :**
- `TeamMember` → `User` (N:1)
- `TeamMember` → `Project` (N:1)
- `TeamMember` ↔ `ProjectRole` (N:N) via `TeamMemberProjectRole`

---

## 🔗 Entités de Support

### **UserGitHubCredentials** — Credentials GitHub

| Nom                | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ------------------ | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| user_id            | UUID       | Utilisateur concerné           | Référence User                         | FK vers User, PK          | MVP      |
| github_access_token| Text       | Token d'accès GitHub           | Token OAuth GitHub                     | Optionnel                 | MVP      |
| github_user_id     | String(100)| ID utilisateur GitHub          | ID numérique GitHub                    | Optionnel                 | MVP      |
| created_at         | DateTime   | Date de création               | ISO 8601                               | Automatique               | MVP      |
| updated_at         | DateTime   | Dernière mise à jour           | ISO 8601                               | Automatique               | MVP      |

**Relations :**
- `UserGitHubCredentials` → `User` (1:1)

### **ProjectExternalLink** — Liens Externes

| Nom        | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ---------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id         | UUID       | Identifiant du lien            | UUID                                   | PK, unique                | MVP      |
| project_id | UUID       | Projet concerné                | Référence Project                      | FK vers Project, obligatoire | MVP   |
| type       | String(50) | Type de lien                   | "github", "website", "documentation"   | Optionnel                 | MVP      |
| url        | Text       | URL du lien                    | URL valide                             | Obligatoire               | MVP      |

**Relations :**
- `ProjectExternalLink` → `Project` (N:1)

### **KeyFeature** — Fonctionnalités Clés

| Nom        | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ---------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id         | UUID       | Identifiant de la fonctionnalité | UUID                                 | PK, unique                | MVP      |
| project_id | UUID       | Projet concerné                | Référence Project                      | FK vers Project, obligatoire | MVP   |
| feature    | String(200)| Nom de la fonctionnalité       | Max 200 caractères                     | Obligatoire               | MVP      |

**Relations :**
- `KeyFeature` → `Project` (N:1)
- `KeyFeature` ↔ `ProjectRoleApplication` (N:N) via `ProjectRoleApplicationKeyFeature`

### **ProjectGoal** — Objectifs de Projet

| Nom        | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ---------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id         | UUID       | Identifiant de l'objectif      | UUID                                   | PK, unique                | MVP      |
| project_id | UUID       | Projet concerné                | Référence Project                      | FK vers Project, obligatoire | MVP   |
| goal       | String(200)| Description de l'objectif      | Max 200 caractères                     | Obligatoire               | MVP      |

**Relations :**
- `ProjectGoal` → `Project` (N:1)
- `ProjectGoal` ↔ `ProjectRoleApplication` (N:N) via `ProjectRoleApplicationProjectGoal`

### **UserSocialLink** — Liens Sociaux

| Nom        | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ---------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id         | UUID       | Identifiant du lien            | UUID                                   | PK, unique                | MVP      |
| user_id    | UUID       | Utilisateur concerné           | Référence User                         | FK vers User, obligatoire  | MVP      |
| type       | String(50) | Type de réseau social          | "github", "twitter", "linkedin"        | Optionnel                 | MVP      |
| url        | Text       | URL du profil                  | URL valide                             | Obligatoire               | MVP      |
| created_at | DateTime   | Date de création               | ISO 8601                               | Automatique               | MVP      |

**Relations :**
- `UserSocialLink` → `User` (N:1)

**Contraintes :**
- `UNIQUE(user_id, type)` : Un utilisateur ne peut avoir qu'un lien par type

---

## 📋 Tables d'Association

### **ProjectTechStack** — Projets ↔ Technologies

| Nom           | Type | Description                    | Contraintes                            |
| ------------- | ---- | ------------------------------ | -------------------------------------- |
| project_id    | UUID | Référence Project              | FK vers Project, PK                    |
| tech_stack_id | UUID | Référence TechStack            | FK vers TechStack, PK                  |

### **UserTechStack** — Utilisateurs ↔ Technologies

| Nom           | Type | Description                    | Contraintes                            |
| ------------- | ---- | ------------------------------ | -------------------------------------- |
| user_id       | UUID | Référence User                 | FK vers User, PK                       |
| tech_stack_id | UUID | Référence TechStack            | FK vers TechStack, PK                  |

### **ProjectCategory** — Projets ↔ Catégories

| Nom          | Type | Description                    | Contraintes                            |
| ------------ | ---- | ------------------------------ | -------------------------------------- |
| project_id   | UUID | Référence Project              | FK vers Project, PK                    |
| category_id  | UUID | Référence Category             | FK vers Category, PK                   |

### **ProjectRoleTechStack** — Rôles ↔ Technologies

| Nom           | Type | Description                    | Contraintes                            |
| ------------- | ---- | ------------------------------ | -------------------------------------- |
| project_role_id | UUID | Référence ProjectRole          | FK vers ProjectRole, PK                |
| tech_stack_id | UUID | Référence TechStack            | FK vers TechStack, PK                  |

### **TeamMemberProjectRole** — Membres ↔ Rôles

| Nom             | Type | Description                    | Contraintes                            |
| --------------- | ---- | ------------------------------ | -------------------------------------- |
| team_member_id  | UUID | Référence TeamMember           | FK vers TeamMember, PK                 |
| project_role_id | UUID | Référence ProjectRole          | FK vers ProjectRole, PK                |

---

## 🎯 Entités de Candidature

### **ProjectRoleApplication** — Candidature

| Nom                 | Type       | Description                    | Valeurs possibles                      | Contraintes               | Priorité |
| ------------------- | ---------- | ------------------------------ | -------------------------------------- | ------------------------- | -------- |
| id                  | UUID       | Identifiant de la candidature  | UUID                                   | PK, unique                | MVP      |
| project_id          | UUID       | Projet concerné                | Référence Project                      | FK vers Project, obligatoire | MVP   |
| project_title       | String(100)| Titre du projet (historique)   | Max 100 caractères                     | Optionnel                 | MVP      |
| project_role_id     | UUID       | Rôle concerné                  | Référence ProjectRole                  | FK vers ProjectRole, obligatoire | MVP |
| project_role_title  | String(100)| Titre du rôle (historique)     | Max 100 caractères                     | Optionnel                 | MVP      |
| project_description | Text       | Description du projet          | Description du projet                  | Optionnel                 | MVP      |
| status              | String(20) | Statut de la candidature       | "pending", "accepted", "rejected", "withdrawn" | Obligatoire        | MVP      |
| motivation_letter   | Text       | Lettre de motivation           | Texte de motivation                    | Optionnel                 | MVP      |
| rejection_reason    | Text       | Raison du rejet                | Raison du rejet                        | Optionnel                 | MVP      |
| applied_at          | DateTime   | Date de candidature            | ISO 8601                               | Automatique               | MVP      |
| created_at          | DateTime   | Date de création               | ISO 8601                               | Automatique               | MVP      |
| updated_at          | DateTime   | Dernière mise à jour           | ISO 8601                               | Automatique               | MVP      |

**Relations :**
- `ProjectRoleApplication` → `Project` (N:1)
- `ProjectRoleApplication` → `ProjectRole` (N:1)
- `ProjectRoleApplication` → `User` (N:1)
- `ProjectRoleApplication` ↔ `KeyFeature` (N:N) via `ProjectRoleApplicationKeyFeature`
- `ProjectRoleApplication` ↔ `ProjectGoal` (N:N) via `ProjectRoleApplicationProjectGoal`

### **ProjectRoleApplicationKeyFeature** — Applications ↔ Fonctionnalités

| Nom                | Type | Description                    | Contraintes                            |
| ------------------ | ---- | ------------------------------ | -------------------------------------- |
| application_id     | UUID | Référence ProjectRoleApplication | FK vers ProjectRoleApplication, PK    |
| key_feature_id     | UUID | Référence KeyFeature           | FK vers KeyFeature, PK                |

### **ProjectRoleApplicationProjectGoal** — Applications ↔ Objectifs

| Nom                | Type | Description                    | Contraintes                            |
| ------------------ | ---- | ------------------------------ | -------------------------------------- |
| application_id     | UUID | Référence ProjectRoleApplication | FK vers ProjectRoleApplication, PK    |
| key_feature_id     | UUID | Référence ProjectGoal          | FK vers ProjectGoal, PK               |

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

### **Contraintes de Validation**

1. **URLs valides** : Tous les champs URL doivent respecter le format URI
2. **Emails valides** : Le champ email doit respecter le format email
3. **Longueurs respectées** : Toutes les limites de caractères sont respectées
4. **Statuts valides** : Les champs enum respectent les valeurs définies

---

## 🚀 Utilisation pour le ML

### **Données d'Entraînement**

1. **TF-IDF** : Utilise le champ `readme` des projets
2. **Mistral-Embed** : Utilise les relations `ProjectTechStack` et `ProjectRoleApplication`
3. **Features** : Les `KeyFeature` et `ProjectGoal` fournissent des métadonnées riches

### **Patterns de Données**

1. **Cohérence** : Toutes les données sont cohérentes entre les entités
2. **Historique** : Les candidatures conservent l'historique des projets/rôles
3. **Relations** : Les relations many-to-many permettent des analyses complexes
4. **Timestamps** : Tous les événements sont timestampés pour l'analyse temporelle