# 📘 Dictionnaire de Données — Open Source Together (Version 3.0)

## 🎯 Segmentation MVP vs Future

Ce dictionnaire présente la structure de données complète d'OST avec trois niveaux de priorité :

- **🔴 MVP (Minimum Viable Product)** : Entités et champs essentiels pour le lancement
- **🔵 Future** : Fonctionnalités avancées à implémenter plus tard
- **🟡 À Discuter** : Points nécessitant une validation équipe avant implémentation

Les étiquettes 🟡🔴 ou 🟡🔵 indiquent les décisions à prendre collectivement entre MVP et Future.

---

## 🎯 Entités Principales

### 🔴 **User** — Utilisateur

| Nom                | Type       | Description                             | Valeurs possibles                      | Contraintes                  | Priorité |
| ------------------ | ---------- | --------------------------------------- | -------------------------------------- | ---------------------------- | -------- |
| id                 | UUID       | Identifiant unique utilisateur          | UUID                                   | PK, unique                   | 🔴 MVP   |
| username           | Texte      | Nom d'utilisateur affiché               | Max 30 caractères                      | Obligatoire, unique          | 🔴 MVP   |
| email              | Texte      | Adresse email                           | Format email                           | Obligatoire, unique          | 🔴 MVP   |
| bio                | Texte      | Bio de l'utilisateur                    | Max 500 caractères                     | Optionnel                    | 🔴 MVP   |
| github_username    | Texte      | Nom d'utilisateur GitHub                | Max 39 caractères                      | Optionnel, unique si présent | 🔴 MVP   |
| linkedin_url       | Texte      | URL du profil LinkedIn                  | Format URL                             | Optionnel                    | 🔴 MVP   |
| portfolio_url      | Texte      | URL du portfolio personnel              | Format URL                             | Optionnel                    | 🔴 MVP   |
| contribution_score | Entier     | Score basé sur les contributions        | ≥ 0                                    | Automatique, calculé         | 🔴 MVP   |
| level              | Texte      | Niveau d'expérience                     | "beginner", "intermediate", "advanced" | Enum, défaut: "beginner"     | 🔴 MVP   |
| is_open_to_hire    | Booléen    | Ouvert aux opportunités de contribution | true/false                             | Défaut: false                | 🔴 MVP   |
| location           | Texte      | Localisation géographique               | Max 100 caractères                     | Optionnel                    | 🔴 MVP   |
| timezone           | Texte      | Fuseau horaire                          | Format IANA (ex: "Europe/Paris")       | Optionnel                    | 🔴 MVP   |
| created_at         | Date/Heure | Date de création du compte              | ISO 8601                               | Automatique                  | 🔴 MVP   |
| updated_at         | Date/Heure | Dernière mise à jour                    | ISO 8601                               | Automatique                  | 🔴 MVP   |

### 🔴 **Project** — Projet

| Nom                     | Type       | Description                          | Valeurs possibles                               | Contraintes               | Priorité |
| ----------------------- | ---------- | ------------------------------------ | ----------------------------------------------- | ------------------------- | -------- |
| id                      | UUID       | Identifiant du projet                | UUID                                            | PK, unique                | 🔴 MVP   |
| owner_id                | UUID       | Propriétaire du projet               | Référence User                                  | FK vers User, obligatoire | 🔴 MVP   |
| title                   | Texte      | Titre du projet                      | Max 100 caractères                              | Obligatoire               | 🔴 MVP   |
| description             | Texte      | Description complète du projet       | Max 2000 caractères                             | Obligatoire               | 🔴 MVP   |
| vision                  | Texte      | Vision et objectifs du projet        | Max 1000 caractères                             | Obligatoire               | 🔴 MVP   |
| github_main_repo        | Texte      | Repository principal GitHub          | URL                                             | Obligatoire               | 🔴 MVP   |
| website_url             | Texte      | Site web du projet                   | URL                                             | Optionnel                 | 🔴 MVP   |
| difficulty              | Texte      | Niveau de difficulté global          | "easy", "medium", "hard"                        | Enum, obligatoire         | 🔴 MVP   |
| status                  | Texte      | État du projet                       | "active", "paused", "completed", "archived"     | Enum, obligatoire         | 🔴 MVP   |
| is_seeking_contributors | Booléen    | Cherche activement des contributeurs | true/false                                      | Défaut: true              | 🔴 MVP   |
| project_type            | Texte      | Format technique du projet           | "web_app", "api", "cli", "mobile_app", "other"  | Enum                      | 🟡🔴     |
| license                 | Texte      | Licence du projet                    | "MIT", "Apache-2.0", "GPL-3.0", "custom"       | Enum                      | 🔴 MVP   |
| stars_count             | Entier     | Nombre d'étoiles GitHub              | ≥ 0                                             | Automatique, synchronisé  | 🔴 MVP   |
| created_at              | Date/Heure | Date de création                     | ISO 8601                                        | Automatique               | 🔴 MVP   |
| updated_at              | Date/Heure | Dernière mise à jour                 | ISO 8601                                        | Automatique               | 🔴 MVP   |

### 🟡🔴 **DomainCategory** — Catégorie de Domaine

| Nom         | Type       | Description                    | Valeurs possibles                                          | Contraintes         | Priorité |
| ----------- | ---------- | ------------------------------ | ---------------------------------------------------------- | ------------------- | -------- |
| id          | UUID       | Identifiant de la catégorie    | UUID                                                       | PK, unique          | 🟡🔴     |
| name        | Texte      | Nom du domaine                 | "Education", "Santé", "Finance", "Gaming", "DevTools"     | Obligatoire, unique | 🟡🔴     |
| description | Texte      | Description du domaine         | Max 500 caractères                                         | Optionnel           | 🟡🔴     |
| icon_url    | Texte      | URL de l'icône du domaine      | Format URL                                                 | Optionnel           | 🟡🔴     |
| created_at  | Date/Heure | Date de création               | ISO 8601                                                   | Automatique         | 🟡🔴     |
| updated_at  | Date/Heure | Dernière mise à jour           | ISO 8601                                                   | Automatique         | 🟡🔴     |

### 🟡🔴 **Skill** — Compétence Métier

| Nom         | Type       | Description                  | Valeurs possibles                                                       | Contraintes         | Priorité |
| ----------- | ---------- | ---------------------------- | ----------------------------------------------------------------------- | ------------------- | -------- |
| id          | UUID       | Identifiant de la compétence | UUID                                                                    | PK, unique          | 🟡🔴     |
| name        | Texte      | Nom de la compétence         | "Product Management", "Marketing", "SEO", "Community Management"       | Obligatoire, unique | 🟡🔴     |
| description | Texte      | Description de la compétence | Max 500 caractères                                                      | Optionnel           | 🟡🔴     |
| icon_url    | Texte      | URL de l'icône               | Format URL                                                              | Optionnel           | 🟡🔴     |
| created_at  | Date/Heure | Date de création             | ISO 8601                                                                | Automatique         | 🟡🔴     |
| updated_at  | Date/Heure | Dernière mise à jour         | ISO 8601                                                                | Automatique         | 🟡🔴     |

### 🔴 **Technology** — Technologie/Outil

| Nom         | Type       | Description                      | Valeurs possibles                                                | Contraintes         | Priorité |
| ----------- | ---------- | -------------------------------- | ---------------------------------------------------------------- | ------------------- | -------- |
| id          | UUID       | Identifiant de la technologie    | UUID                                                             | PK, unique          | 🔴 MVP   |
| name        | Texte      | Nom de la technologie/outil      | "React", "Python", "Figma", "Docker", "Slack", "Notion"        | Obligatoire, unique | 🔴 MVP   |
| description | Texte      | Description de la technologie    | Max 500 caractères                                               | Optionnel           | 🔴 MVP   |
| icon_url    | Texte      | URL de l'icône                   | Format URL                                                       | Optionnel           | 🔴 MVP   |
| category    | Texte      | Catégorie de technologie         | "frontend", "backend", "design", "devops", "business", "other"  | Enum                | 🔵 Future |
| created_at  | Date/Heure | Date de création                 | ISO 8601                                                         | Automatique         | 🔴 MVP   |
| updated_at  | Date/Heure | Dernière mise à jour             | ISO 8601                                                         | Automatique         | 🔴 MVP   |

### 🔴 **ProjectRole** — Rôle Projet

| Nom                  | Type       | Description                        | Valeurs possibles                     | Contraintes             | Priorité |
| -------------------- | ---------- | ---------------------------------- | ------------------------------------- | ----------------------- | -------- |
| id                   | UUID       | Identifiant du rôle dans un projet | UUID                                  | PK, unique              | 🔴 MVP   |
| project_id           | UUID       | Projet concerné                    | Référence Project                     | FK vers Project         | 🔴 MVP   |
| title                | Texte      | Titre du rôle                      | "Frontend Lead", "UX Designer"        | Obligatoire             | 🔴 MVP   |
| description          | Texte      | Description détaillée du rôle      | Max 1000 caractères                   | Obligatoire             | 🔴 MVP   |
| responsibility_level | Texte      | Niveau de responsabilité           | "contributor", "maintainer", "lead"   | Enum                    | 🔴 MVP   |
| time_commitment      | Texte      | Engagement temps estimé            | "few_hours", "part_time", "full_time" | Enum                    | 🔴 MVP   |
| slots_available      | Entier     | Nombre de places disponibles       | ≥ 0                                   | Obligatoire             | 🔴 MVP   |
| slots_filled         | Entier     | Nombre de places occupées          | ≥ 0                                   | Calculé automatiquement | 🔴 MVP   |
| experience_required  | Texte      | Expérience requise                 | "none", "some", "experienced"         | Enum                    | 🔴 MVP   |
| created_at           | Date/Heure | Date de création du rôle           | ISO 8601                              | Automatique             | 🔴 MVP   |

### 🔴 **GoodFirstIssue**  

| Nom              | Type       | Description                   | Valeurs possibles                                        | Contraintes             | Priorité |
| ---------------- | ---------- | ----------------------------- | -------------------------------------------------------- | ----------------------- | -------- |
| id               | UUID       | Identifiant de l'issue        | UUID                                                     | PK, unique              | 🔴 MVP   |
| project_id       | UUID       | Projet concerné               | Référence Project                                        | FK vers Project         | 🔴 MVP   |
| created_by       | UUID       | Mainteneur qui a créé l'issue | Référence User                                           | FK vers User            | 🔴 MVP   |
| title            | Texte      | Titre de l'issue              | Max 200 caractères                                       | Obligatoire             | 🔴 MVP   |
| description      | Texte      | Description détaillée         | Max 2000 caractères                                      | Obligatoire             | 🔴 MVP   |
| github_issue_url | Texte      | Lien vers l'issue GitHub      | URL                                                      | Optionnel               | 🔴 MVP   |
| estimated_time   | Texte      | Temps estimé                  | "30min", "1h", "2h", "4h", "1day"                        | Enum                    | 🔵 Future   |
| difficulty       | Texte      | Difficulté de l'issue         | "very_easy", "easy", "medium"                            | Enum                    | 🔴 MVP   |
| status           | Texte      | État de l'issue               | "open", "assigned", "in_progress", "completed", "closed" | Enum                    | 🔴 MVP   |
| assigned_to      | UUID       | Utilisateur assigné           | Référence User                                           | FK vers User, optionnel | 🔴 MVP   |
| is_ai_generated  | Booléen    | Issue générée par IA          | true/false                                               | Défaut: false           | 🔴 MVP   |
| created_at       | Date/Heure | Date de création              | ISO 8601                                                 | Automatique             | 🔴 MVP   |
| completed_at     | Date/Heure | Date de completion            | ISO 8601                                                 | Optionnel               | 🔴 MVP   |

### 🔴 **Contribution** — Contribution

| Nom             | Type       | Description                    | Valeurs possibles                                                | Contraintes     | Priorité |
| --------------- | ---------- | ------------------------------ | ---------------------------------------------------------------- | --------------- | -------- |
| id              | UUID       | Identifiant de la contribution | UUID                                                             | PK, unique      | 🔴 MVP   |
| user_id         | UUID       | Contributeur                   | Référence User                                                   | FK vers User    | 🔴 MVP   |
| project_id      | UUID       | Projet concerné                | Référence Project                                                | FK vers Project | 🔴 MVP   |
| issue_id        | UUID       | Issue liée (si applicable)     | Référence GoodFirstIssue                                         | FK, optionnel   | 🔴 MVP   |
| type            | Texte      | Type de contribution           | "code", "design", "documentation", "bug_fix", "feature", "other" | Enum            | 🔴 MVP   |
| title           | Texte      | Titre de la contribution       | Max 200 caractères                                               | Obligatoire     | 🔴 MVP   |
| description     | Texte      | Description de la contribution | Max 1000 caractères                                              | Optionnel       | 🔴 MVP   |
| github_pr_url   | Texte      | URL de la Pull Request         | URL                                                              | Optionnel       | 🔴 MVP   |
| status          | Texte      | Statut de la contribution      | "submitted", "reviewed", "merged", "rejected"                    | Enum            | 🔴 MVP   |
| reviewed_by     | UUID       | Reviewer                       | Référence User                                                   | FK, optionnel   | 🔴 MVP   |
| submitted_at    | Date/Heure | Date de soumission             | ISO 8601                                                         | Automatique     | 🔴 MVP   |
| merged_at       | Date/Heure | Date de merge                  | ISO 8601                                                         | Optionnel       | 🔴 MVP   |

### 🟡🔴 **LinkedRepository** — Repository Lié

| Nom         | Type       | Description                    | Valeurs possibles            | Contraintes     | Priorité |
| ----------- | ---------- | ------------------------------ | ---------------------------- | --------------- | -------- |
| id          | UUID       | Identifiant                    | UUID                         | PK, unique      | 🟡🔴     |
| project_id  | UUID       | Projet parent                  | Référence Project            | FK vers Project | 🟡🔴     |
| github_url  | Texte      | URL du repository              | URL GitHub                   | Obligatoire     | 🟡🔴     |
| name        | Texte      | Nom du repository              | Max 100 caractères           | Obligatoire     | 🟡🔴     |
| description | Texte      | Description du repo            | Max 500 caractères           | Optionnel       | 🟡🔴     |
| is_main     | Booléen    | Repository principal du projet | true/false                   | Défaut: false   | 🟡🔴     |
| language    | Texte      | Langage principal              | "JavaScript", "Python", etc. | Optionnel       | 🟡🔴     |
| stars_count | Entier     | Nombre d'étoiles               | ≥ 0                          | Synchronisé     | 🟡🔴     |
| last_sync   | Date/Heure | Dernière synchronisation       | ISO 8601                     | Automatique     | 🟡🔴     |

---

## 🔗 Entités de Liaison

### 🔴 **UserSkill** — Compétences Utilisateur

| Nom               | Type    | Description           | Valeurs possibles                                         | Contraintes   | Priorité |
| ----------------- | ------- | --------------------- | --------------------------------------------------------- | ------------- | -------- |
| id                | UUID    | Identifiant           | UUID                                                      | PK, unique    | 🔴 MVP   |
| user_id           | UUID    | Utilisateur           | Référence User                                            | FK vers User  | 🔴 MVP   |
| skill_id          | UUID    | Compétence            | Référence Skill                                           | FK vers Skill | 🔴 MVP   |
| proficiency_level | Texte   | Niveau de maîtrise    | "learning", "basic", "intermediate", "advanced", "expert" | Enum          | 🔴 MVP   |
| is_primary        | Booléen | Compétence principale | true/false                                                | Défaut: false | 🔴 MVP   |
| created_at        | Date    | Date d'ajout          | ISO 8601                                                  | Automatique   | 🔴 MVP   |

### 🔴 **UserTechnology** — Technologies Utilisateur

| Nom               | Type    | Description              | Valeurs possibles                                         | Contraintes        | Priorité |
| ----------------- | ------- | ------------------------ | --------------------------------------------------------- | ------------------ | -------- |
| id                | UUID    | Identifiant              | UUID                                                      | PK, unique         | 🔴 MVP   |
| user_id           | UUID    | Utilisateur              | Référence User                                            | FK vers User       | 🔴 MVP   |
| technology_id     | UUID    | Technologie              | Référence Technology                                      | FK vers Technology | 🔴 MVP   |
| proficiency_level | Texte   | Niveau de maîtrise       | "learning", "basic", "intermediate", "advanced", "expert" | Enum               | 🔴 MVP   |
| is_primary        | Booléen | Technologie principale   | true/false                                                | Défaut: false      | 🔴 MVP   |
| created_at        | Date    | Date d'ajout             | ISO 8601                                                  | Automatique        | 🔴 MVP   |

### 🔴 **Application** — Candidature

| Nom              | Type       | Description                     | Valeurs possibles                              | Contraintes             | Priorité |
| ---------------- | ---------- | ------------------------------- | ---------------------------------------------- | ----------------------- | -------- |
| id               | UUID       | Identifiant de la candidature   | UUID                                           | PK, unique              | 🔴 MVP   |
| user_id          | UUID       | Utilisateur qui postule         | Référence User                                 | FK vers User            | 🔴 MVP   |
| project_role_id  | UUID       | Rôle auquel il postule          | Référence ProjectRole                          | FK vers ProjectRole     | 🔴 MVP   |
| motivation_message | Texte    | Message de motivation du candidat | Max 1000 caractères                          | Optionnel               | 🟡🔴     |
| availability     | Texte      | Disponibilité                   | "immediate", "within_week", "within_month"     | Enum                    | 🔴 MVP   |
| status           | Texte      | Statut de la candidature        | "pending", "accepted", "rejected", "withdrawn" | Enum, obligatoire       | 🔴 MVP   |
| reviewed_by      | UUID       | Qui a évalué la candidature     | Référence User                                 | FK vers User, optionnel | 🔴 MVP   |
| review_message   | Texte      | Message de retour               | Max 500 caractères                             | Optionnel               | 🔴 MVP   |
| applied_at       | Date/Heure | Date de postulation             | ISO 8601                                       | Automatique             | 🔴 MVP   |
| reviewed_at      | Date/Heure | Date d'évaluation               | ISO 8601                                       | Optionnel               | 🔴 MVP   |

### 🔴 **TeamMember** — Membre d'Équipe

| Nom                 | Type       | Description                    | Valeurs possibles            | Contraintes             | Priorité |
| ------------------- | ---------- | ------------------------------ | ---------------------------- | ----------------------- | -------- |
| id                  | UUID       | Identifiant du membre          | UUID                         | PK, unique              | 🔴 MVP   |
| user_id             | UUID       | Utilisateur membre             | Référence User               | FK vers User            | 🔴 MVP   |
| project_id          | UUID       | Projet concerné                | Référence Project            | FK vers Project         | 🔴 MVP   |
| project_role_id     | UUID       | Rôle dans le projet            | Référence ProjectRole        | FK vers ProjectRole     | 🔴 MVP   |
| status              | Texte      | Statut dans l'équipe           | "active", "inactive", "left" | Enum                    | 🔴 MVP   |
| contributions_count | Entier     | Nombre de contributions        | ≥ 0                          | Calculé automatiquement | 🔴 MVP   |
| joined_at           | Date/Heure | Date d'entrée dans l'équipe    | ISO 8601                     | Automatique             | 🔴 MVP   |
| left_at             | Date/Heure | Date de sortie (si applicable) | ISO 8601                     | Optionnel               | 🔴 MVP   |

### 🔵 **CommunityMember** — Membre Communauté

| Nom                   | Type       | Description                | Valeurs possibles | Contraintes     | Priorité    |
| --------------------- | ---------- | -------------------------- | ----------------- | --------------- | ----------- |
| id                    | UUID       | Identifiant                | UUID              | PK, unique      | 🔵 Future   |
| user_id               | UUID       | Utilisateur follower       | Référence User    | FK vers User    | 🔵 Future   |
| project_id            | UUID       | Projet suivi               | Référence Project | FK vers Project | 🔵 Future   |
| followed_at           | Date/Heure | Date de début de suivi     | ISO 8601          | Automatique     | 🔵 Future   |
| notifications_enabled | Booléen    | Notifications activées     | true/false        | Défaut: true    | 🔵 Future   |

### 🟡🔵 **ProjectDomainCategory** — Domaines Projet

| Nom                | Type    | Description                    | Valeurs possibles       | Contraintes              | Priorité    |
| ------------------ | ------- | ------------------------------ | ----------------------- | ------------------------ | ----------- |
| id                 | UUID    | Identifiant                    | UUID                    | PK, unique               | 🟡🔵        |
| project_id         | UUID    | Projet concerné                | Référence Project       | FK vers Project          | 🟡🔵        |
| domain_category_id | UUID    | Catégorie de domaine           | Référence DomainCategory | FK vers DomainCategory   | 🟡🔵        |
| is_primary         | Booléen | Domaine principal du projet    | true/false              | Défaut: false            | 🟡🔵        |

### 🔴 **ProjectSkill** — Compétences Projet

| Nom        | Type    | Description                | Valeurs possibles | Contraintes   | Priorité |
| ---------- | ------- | -------------------------- | ----------------- | ------------- | -------- |
| id         | UUID    | Identifiant                | UUID              | PK, unique    | 🔴 MVP   |
| project_id | UUID    | Projet concerné            | Référence Project | FK vers Project | 🔴 MVP |
| skill_id   | UUID    | Compétence utilisée        | Référence Skill   | FK vers Skill | 🔴 MVP   |
| is_primary | Booléen | Compétence principale      | true/false        | Défaut: false | 🔴 MVP   |

### 🔴 **ProjectTechnology** — Technologies Projet

| Nom           | Type    | Description                | Valeurs possibles    | Contraintes        | Priorité |
| ------------- | ------- | -------------------------- | -------------------- | ------------------ | -------- |
| id            | UUID    | Identifiant                | UUID                 | PK, unique         | 🔴 MVP   |
| project_id    | UUID    | Projet concerné            | Référence Project    | FK vers Project    | 🔴 MVP   |
| technology_id | UUID    | Technologie utilisée       | Référence Technology | FK vers Technology | 🔴 MVP   |
| is_primary    | Booléen | Technologie principale     | true/false           | Défaut: false      | 🔴 MVP   |

### 🟡🔴 **ProjectRoleSkill** — Compétences Rôle

| Nom               | Type    | Description                           | Valeurs possibles                   | Contraintes         | Priorité |
| ----------------- | ------- | ------------------------------------- | ----------------------------------- | ------------------- | -------- |
| id                | UUID    | Identifiant                           | UUID                                | PK, unique          | 🟡🔴     |
| project_role_id   | UUID    | Rôle concerné                         | Référence ProjectRole               | FK vers ProjectRole | 🟡🔴     |
| skill_id          | UUID    | Compétence requise                    | Référence Skill                     | FK vers Skill       | 🟡🔴     |
| proficiency_level | Texte   | Niveau requis                         | "basic", "intermediate", "advanced" | Enum                | 🟡🔴     |
| is_required       | Booléen | Compétence obligatoire ou optionnelle | true/false                          | Défaut: true        | 🟡🔴     |

### 🔴 **ProjectRoleTechnology** — Technologies Rôle

| Nom               | Type    | Description                            | Valeurs possibles                   | Contraintes         | Priorité |
| ----------------- | ------- | -------------------------------------- | ----------------------------------- | ------------------- | -------- |
| id                | UUID    | Identifiant                            | UUID                                | PK, unique          | 🔴 MVP   |
| project_role_id   | UUID    | Rôle concerné                          | Référence ProjectRole               | FK vers ProjectRole | 🔴 MVP   |
| technology_id     | UUID    | Technologie requise                    | Référence Technology                | FK vers Technology  | 🔴 MVP   |
| proficiency_level | Texte   | Niveau requis                          | "basic", "intermediate", "advanced" | Enum                | 🔴 MVP   |
| is_required       | Booléen | Technologie obligatoire ou optionnelle | true/false                          | Défaut: true        | 🔴 MVP   |

### 🟡🔴 **IssueSkill** — Compétences Issue

| Nom        | Type    | Description           | Valeurs possibles        | Contraintes            | Priorité |
| ---------- | ------- | --------------------- | ------------------------ | ---------------------- | -------- |
| id         | UUID    | Identifiant           | UUID                     | PK, unique             | 🟡🔴     |
| issue_id   | UUID    | Issue concernée       | Référence GoodFirstIssue | FK vers GoodFirstIssue | 🟡🔴     |
| skill_id   | UUID    | Compétence requise    | Référence Skill          | FK vers Skill          | 🟡🔴     |
| is_primary | Booléen | Compétence principale | true/false               | Défaut: false          | 🟡🔴     |

### 🔴 **IssueTechnology** — Technologies Issue

| Nom           | Type    | Description              | Valeurs possibles        | Contraintes            | Priorité |
| ------------- | ------- | ------------------------ | ------------------------ | ---------------------- | -------- |
| id            | UUID    | Identifiant              | UUID                     | PK, unique             | 🔴 MVP   |
| issue_id      | UUID    | Issue concernée          | Référence GoodFirstIssue | FK vers GoodFirstIssue | 🔴 MVP   |
| technology_id | UUID    | Technologie nécessaire   | Référence Technology     | FK vers Technology     | 🔴 MVP   |
| is_primary    | Booléen | Technologie principale   | true/false               | Défaut: false          | 🔴 MVP   |

---

## 🔍 Contraintes d'Intégrité

### **Contraintes Métier**

1. **Propriété de projet** : Un utilisateur ne peut pas postuler à un rôle dans son propre projet
2. **Unicité des membres** : Un utilisateur ne peut occuper qu'un seul rôle par projet
3. **Slots disponibles** : Le nombre de membres actifs ne peut pas dépasser les slots disponibles
4. **Cohérence des contributions** : Une contribution ne peut être liée qu'à une issue du même projet
5. **Compétences ou technologies obligatoires** : Un ProjectRole doit avoir au minimum une compétence ou technologie associée
6. **Assignation unique** : Une GoodFirstIssue ne peut être assignée qu'à un seul utilisateur à la fois

### **Contraintes Techniques**

1. **Unicité conditionnelle** : github_username unique si non null
2. **Validation des URLs** : Tous les champs URL doivent respecter le format URI
3. **Cohérence temporelle** : reviewed_at >= applied_at pour les candidatures
4. **Scores positifs** : contribution_score >= 0
5. **Technologies valides** : Chaque Technology doit respecter le catalogue OST
6. **Niveaux cohérents** : proficiency_level doit respecter l'ordre hiérarchique

### **Contraintes de Statut**

1. **Progression des candidatures** : pending → accepted/rejected (pas de retour en arrière)
2. **Statut des issues** : open → assigned → in_progress → completed/closed
3. **Statut des contributions** : submitted → reviewed → merged/rejected
4. **Statut des projets** : Cohérence avec is_seeking_contributors

---

## 📊 Points d'Attention Implementation

### **🔴 MVP - Décisions Prises**

- **Architecture Skill/Technology** : Distinction claire métier vs outils
- **Catalogue unifié** : Technologies techniques ET métier dans Technology
- **Validation** : Auto-déclaration libre pour MVP
- **Assignation issues** : Système simple 1:1 sans réservation
- **Contributions** : Tracking interne pour scoring

### **🟡 Décisions à Valider**

- **motivation_message** : Obligatoire/Optionnel/Configurable par owner ?
- **Limitation candidatures** : Nombre max par utilisateur/projet ?
- **ProjectType** : Obligatoire MVP ou peut attendre ?
- **LinkedRepository** : Essentiel MVP pour projets multi-repos ?
- **DomainCategory** : Nécessaire dès MVP pour discovery ?

### **🔵 Future - Évolutions Prévues**

- **Catégorisation** : TechnologyCategory pour organisation
- **Validation avancée** : Endorsement, quiz, certification
- **Community features** : Suivi projets, notifications
- **Gamification** : Scoring avancé, badges, leaderboards
- **Intégration GitHub** : Sync automatique contributions