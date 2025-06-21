### 📘 Dictionnaire de données — Open Source Together (Version 2.0)

## 🎯 Segmentation MVP vs Future

Ce dictionnaire présente deux niveaux de fonctionnalités :

- **🔴 MVP (Minimum Viable Product)** : Champs essentiels pour le lancement
- **🔵 Future** : Fonctionnalités avancées à implémenter plus tard
- **🟡 À Discuter** : Points nécessitant une validation équipe avant implémentation

---

#### 🔹 Utilisateur (User)

| Nom                | Type       | Description                             | Valeurs possibles                      | Contraintes                  | Priorité |
| ------------------ | ---------- | --------------------------------------- | -------------------------------------- | ---------------------------- | -------- |
| id_user            | UUID       | Identifiant unique utilisateur          | UUID                                   | PK, unique                   | MVP      |
| username           | Texte      | Nom d'utilisateur affiché               | Max 30 caractères                      | Obligatoire, unique          | MVP      |
| email              | Texte      | Adresse email                           | Format email                           | Obligatoire, unique          | MVP      |
| bio                | Texte      | Bio de l'utilisateur                    | Max 500 caractères                     | Optionnel                    | MVP      |
| github_username    | Texte      | Nom d'utilisateur GitHub                | Max 39 caractères                      | Optionnel, unique si présent | MVP      |
| linkedin_url       | Texte      | URL du profil LinkedIn                  | Format URL                             | Optionnel                    | MVP      |
| github_url         | Texte      | URL du profil Github                    | Format URL                             | Optionnel                    | MVP      |
| portfolio_url      | Texte      | URL du portfolio personnel              | Format URL                             | Optionnel                    | MVP      |
| contribution_score | Entier     | Score basé sur les contributions        | ≥ 0                                    | Automatique, calculé         | MVP      |
| level              | Texte      | Niveau d'expérience                     | "beginner", "intermediate", "advanced" | Enum, défaut: "beginner"     | MVP      |
| is_open_to_hire    | Booléen    | Ouvert aux opportunités de contribution | true/false                             | Défaut: false                | MVP      |
| location           | Texte      | Localisation géographique               | Max 100 caractères                     | Optionnel                    | MVP      |
| timezone           | Texte      | Fuseau horaire                          | Format IANA (ex: "Europe/Paris")       | Optionnel                    | MVP      |
| created_at         | Date/Heure | Date de création du compte              | ISO 8601                               | Automatique                  | MVP      |
| updated_at         | Date/Heure | Dernière mise à jour                    | ISO 8601                               | Automatique                  | MVP      |

#### 🔹 Projet (Project)

| Nom                     | Type       | Description                          | Valeurs possibles                                      | Contraintes               | Priorité |
| ----------------------- | ---------- | ------------------------------------ | ------------------------------------------------------ | ------------------------- | -------- |
| id_project              | UUID       | Identifiant du projet                | UUID                                                   | PK, unique                | MVP      |
| owner_id                | UUID       | Propriétaire du projet               | Référence User                                         | FK vers User, obligatoire | MVP      |
| title                   | Texte      | Titre du projet                      | Max 100 caractères                                     | Obligatoire               | MVP      |
| description             | Texte      | Description complète du projet       | Max 2000 caractères                                    | Obligatoire               | MVP      |
| vision                  | Texte      | Vision et objectifs du projet        | Max 1000 caractères                                    | Obligatoire               | MVP      |
| github_main_repo        | Texte      | Repository principal GitHub          | URL                                                    | Obligatoire               | MVP      |
| website_url             | Texte      | Site web du projet                   | URL                                                    | Optionnel                 | MVP      |
| documentation_url       | Texte      | URL de la documentation              | URL                                                    | Optionnel                 | MVP      |
| difficulty              | Texte      | Niveau de difficulté global          | "easy", "medium", "hard"                               | Enum, obligatoire         | MVP      |
| status                  | Texte      | État du projet                       | "active", "paused", "completed", "archived"            | Enum, obligatoire         | MVP      |
| is_seeking_contributors | Booléen    | Cherche activement des contributeurs | true/false                                             | Défaut: true              | MVP      |
| project_type            | Texte      | Type de projet                       | "library", "application", "tool", "framework", "other" | Enum                      | MVP      |
| license                 | Texte      | Licence du projet                    | "MIT", "Apache-2.0", "GPL-3.0", "custom", "other"      | Enum                      | MVP      |
| stars_count             | Entier     | Nombre d'étoiles GitHub              | ≥ 0                                                    | Automatique, synchronisé  | MVP      |
| contributors_count      | Entier     | Nombre de contributeurs actifs       | ≥ 0                                                    | Calculé                   | MVP      |
| created_at              | Date/Heure | Date de création                     | ISO 8601                                               | Automatique               | MVP      |
| updated_at              | Date/Heure | Dernière mise à jour                 | ISO 8601                                               | Automatique               | MVP      |

#### 🔹 Catégorie de Compétence (SkillCategory)

| Nom         | Type       | Description                    | Valeurs possibles                                  | Contraintes         | Priorité |
| ----------- | ---------- | ------------------------------ | -------------------------------------------------- | ------------------- | -------- |
| id_category | UUID       | Identifiant de la catégorie    | UUID                                               | PK, unique          | MVP      |
| name        | Texte      | Nom de la catégorie            | "Frontend", "Backend", "Design", "Marketing", etc. | Obligatoire, unique | MVP      |
| description | Texte      | Description de la catégorie    | Max 500 caractères                                 | Optionnel           | MVP      |
| icon_url    | Texte      | URL de l'icône de la catégorie | Format URL                                         | Optionnel           | MVP      |
| created_at  | Date/Heure | Date de création               | ISO 8601                                           | Automatique         | MVP      |
| updated_at  | Date/Heure | Dernière mise à jour           | ISO 8601                                           | Automatique         | MVP      |

**🔵 Champs Future ? :**

- `color` : Couleur hexadécimale pour l'UI (pas prioritaire)
- `sort_order` : Ordre d'affichage (ORDER BY name suffit)
- `is_active` : Gestion activité/désactivation (pas critique MVP)

#### 🔹 Compétence (Skill)

| Nom               | Type       | Description                  | Valeurs possibles                 | Contraintes           | Priorité |
| ----------------- | ---------- | ---------------------------- | --------------------------------- | --------------------- | -------- |
| id_skill          | UUID       | Identifiant de la compétence | UUID                              | PK, unique            | MVP      |
| skill_category_id | UUID       | Catégorie de la compétence   | Référence SkillCategory           | FK vers SkillCategory | MVP      |
| name              | Texte      | Nom de la compétence         | "React", "UX Design", "SEO", etc. | Obligatoire, unique   | MVP      |
| description       | Texte      | Description de la compétence | Max 500 caractères                | Optionnel             | MVP      |
| icon_url          | Texte      | URL de l'icône               | Format URL                        | Optionnel             | MVP      |
| is_technical      | Booléen    | Compétence technique ou non  | true/false                        | Défaut: true          | MVP      |
| created_at        | Date/Heure | Date de création             | ISO 8601                          | Automatique           | MVP      |
| updated_at        | Date/Heure | Dernière mise à jour         | ISO 8601                          | Automatique           | MVP      |

**🔵 Champs Future ?:**

- `color` : Couleur hexadécimale (UI non prioritaire)
- `popularity_score` : Score de popularité (calculable plus tard avec vraies données)
- `is_active` : Gestion activité (pas critique MVP, toutes actives par défaut)

#### 🔹 Rôle Projet (ProjectRole)

| Nom                  | Type       | Description                        | Valeurs possibles                     | Contraintes             | Priorité |
| -------------------- | ---------- | ---------------------------------- | ------------------------------------- | ----------------------- | -------- |
| id_project_role      | UUID       | Identifiant du rôle dans un projet | UUID                                  | PK, unique              | MVP      |
| project_id           | UUID       | Projet concerné                    | Référence Project                     | FK vers Project         | MVP      |
| title                | Texte      | Titre du rôle                      | "Frontend Lead", "UX Designer"        | Obligatoire             | MVP      |
| description          | Texte      | Description détaillée du rôle      | Max 1000 caractères                   | Obligatoire             | MVP      |
| responsibility_level | Texte      | Niveau de responsabilité           | "contributor", "maintainer", "lead"   | Enum                    | MVP      |
| time_commitment      | Texte      | Engagement temps estimé            | "few_hours", "part_time", "full_time" | Enum                    | MVP      |
| slots_available      | Entier     | Nombre de places disponibles       | ≥ 0                                   | Obligatoire             | MVP      |
| slots_filled         | Entier     | Nombre de places occupées          | ≥ 0                                   | Calculé automatiquement | MVP      |
| experience_required  | Texte      | Expérience requise                 | "none", "some", "experienced"         | Enum                    | MVP      |
| created_at           | Date/Heure | Date de création du rôle           | ISO 8601                              | Automatique             | MVP      |


#### 🔹 Compétences Requises pour un Rôle (ProjectRoleSkill)

| Nom               | Type    | Description                           | Valeurs possibles                   | Contraintes         | Priorité |
| ----------------- | ------- | ------------------------------------- | ----------------------------------- | ------------------- | -------- |
| id                | UUID    | Identifiant                           | UUID                                | PK, unique          | MVP      |
| project_role_id   | UUID    | Rôle concerné                         | Référence ProjectRole               | FK vers ProjectRole | MVP      |
| skill_id          | UUID    | Compétence requise                    | Référence Skill                     | FK vers Skill       | MVP      |
| proficiency_level | Texte   | Niveau requis                         | "basic", "intermediate", "advanced" | Enum                | MVP      |
| is_required       | Booléen | Compétence obligatoire ou optionnelle | true/false                          | Défaut: true        | MVP      |

#### 🔹 Candidature (Application)

| Nom             | Type       | Description                   | Valeurs possibles                              | Contraintes             | Priorité |
| --------------- | ---------- | ----------------------------- | ---------------------------------------------- | ----------------------- | -------- |
| id_application  | UUID       | Identifiant de la candidature | UUID                                           | PK, unique              | MVP      |
| user_id         | UUID       | Utilisateur qui postule       | Référence User                                 | FK vers User            | MVP      |
| project_role_id | UUID       | Rôle auquel il postule        | Référence ProjectRole                          | FK vers ProjectRole     | MVP      |
| portfolio_links | JSON       | Liens vers portfolio/travaux  | Array d'URLs                                   | Optionnel               | MVP      |
| availability    | Texte      | Disponibilité                 | "immediate", "within_week", "within_month"     | Enum                    | MVP      |
| status          | Texte      | Statut de la candidature      | "pending", "accepted", "rejected", "withdrawn" | Enum, obligatoire       | MVP      |
| reviewed_by     | UUID       | Qui a évalué la candidature   | Référence User                                 | FK vers User, optionnel | MVP      |
| review_message  | Texte      | Message de retour             | Max 500 caractères                             | Optionnel               | MVP      |
| applied_at      | Date/Heure | Date de postulation           | ISO 8601                                       | Automatique             | MVP      |
| reviewed_at     | Date/Heure | Date d'évaluation             | ISO 8601                                       | Optionnel               | MVP      |

**🟡 À Discuter avec l'équipe :**

- `motivation_message` : Message de motivation du candidat
  - **Pour** : Améliore la qualité des candidatures, aide le choix des owners
  - **Contre** : Ajoute de la friction, peut décourager les candidatures spontanées
  - **Options** : Obligatoire / Optionnel / Configurable par projet owner
  - **Décision requise** : Validation équipe sur l'approche

#### 🔹 Membre d'Équipe (TeamMember)

| Nom                 | Type       | Description                    | Valeurs possibles            | Contraintes             | Priorité |
| ------------------- | ---------- | ------------------------------ | ---------------------------- | ----------------------- | -------- |
| id_team_member      | UUID       | Identifiant du membre          | UUID                         | PK, unique              | MVP      |
| user_id             | UUID       | Utilisateur membre             | Référence User               | FK vers User            | MVP      |
| project_id          | UUID       | Projet concerné                | Référence Project            | FK vers Project         | MVP      |
| project_role_id     | UUID       | Rôle dans le projet            | Référence ProjectRole        | FK vers ProjectRole     | MVP      |
| status              | Texte      | Statut dans l'équipe           | "active", "inactive", "left" | Enum                    | MVP      |
| contributions_count | Entier     | Nombre de contributions        | ≥ 0                          | Calculé automatiquement | MVP      |
| joined_at           | Date/Heure | Date d'entrée dans l'équipe    | ISO 8601                     | Automatique             | MVP      |
| left_at             | Date/Heure | Date de sortie (si applicable) | ISO 8601                     | Optionnel               | MVP      |

#### 🔹 Good First Issue

| Nom              | Type       | Description                   | Valeurs possibles                                        | Contraintes             | Priorité |
| ---------------- | ---------- | ----------------------------- | -------------------------------------------------------- | ----------------------- | -------- |
| id_issue         | UUID       | Identifiant de l'issue        | UUID                                                     | PK, unique              | MVP      |
| project_id       | UUID       | Projet concerné               | Référence Project                                        | FK vers Project         | MVP      |
| created_by       | UUID       | Mainteneur qui a créé l'issue | Référence User                                           | FK vers User            | MVP      |
| title            | Texte      | Titre de l'issue              | Max 200 caractères                                       | Obligatoire             | MVP      |
| description      | Texte      | Description détaillée         | Max 2000 caractères                                      | Obligatoire             | MVP      |
| github_issue_url | Texte      | Lien vers l'issue GitHub      | URL                                                      | Optionnel               | MVP      |
| estimated_time   | Texte      | Temps estimé                  | "30min", "1h", "2h", "4h", "1day"                        | Enum                    | MVP      |
| difficulty       | Texte      | Difficulté de l'issue         | "very_easy", "easy", "medium"                            | Enum                    | MVP      |
| status           | Texte      | État de l'issue               | "open", "assigned", "in_progress", "completed", "closed" | Enum                    | MVP      |
| assigned_to      | UUID       | Utilisateur assigné           | Référence User                                           | FK vers User, optionnel | MVP      |
| is_ai_generated  | Booléen    | Issue générée par IA          | true/false                                               | Défaut: false           | MVP      |
| created_at       | Date/Heure | Date de création              | ISO 8601                                                 | Automatique             | MVP      |
| completed_at     | Date/Heure | Date de completion            | ISO 8601                                                 | Optionnel               | MVP      |

#### 🔹 Compétences requises pour une Issue (IssueSkill)

| Nom        | Type    | Description           | Valeurs possibles        | Contraintes            | Priorité |
| ---------- | ------- | --------------------- | ------------------------ | ---------------------- | -------- |
| id         | UUID    | Identifiant           | UUID                     | PK, unique             | MVP      |
| issue_id   | UUID    | Issue concernée       | Référence GoodFirstIssue | FK vers GoodFirstIssue | MVP      |
| skill_id   | UUID    | Compétence requise    | Référence Skill          | FK vers Skill          | MVP      |
| is_primary | Booléen | Compétence principale | true/false               | Défaut: false          | MVP      |

#### 🔹 Contribution

| Nom             | Type       | Description                    | Valeurs possibles                                                | Contraintes     | Priorité |
| --------------- | ---------- | ------------------------------ | ---------------------------------------------------------------- | --------------- | -------- |
| id_contribution | UUID       | Identifiant de la contribution | UUID                                                             | PK, unique      | MVP      |
| user_id         | UUID       | Contributeur                   | Référence User                                                   | FK vers User    | MVP      |
| project_id      | UUID       | Projet concerné                | Référence Project                                                | FK vers Project | MVP      |
| issue_id        | UUID       | Issue liée (si applicable)     | Référence GoodFirstIssue                                         | FK, optionnel   | MVP      |
| type            | Texte      | Type de contribution           | "code", "design", "documentation", "bug_fix", "feature", "other" | Enum            | MVP      |
| title           | Texte      | Titre de la contribution       | Max 200 caractères                                               | Obligatoire     | MVP      |
| description     | Texte      | Description de la contribution | Max 1000 caractères                                              | Optionnel       | MVP      |
| github_pr_url   | Texte      | URL de la Pull Request         | URL                                                              | Optionnel       | MVP      |
| status          | Texte      | Statut de la contribution      | "submitted", "reviewed", "merged", "rejected"                    | Enum            | MVP      |
| reviewed_by     | UUID       | Reviewer                       | Référence User                                                   | FK, optionnel   | MVP      |
| submitted_at    | Date/Heure | Date de soumission             | ISO 8601                                                         | Automatique     | MVP      |
| merged_at       | Date/Heure | Date de merge                  | ISO 8601                                                         | Optionnel       | MVP      |

#### 🔹 Compétences Utilisateur (UserSkill)

| Nom               | Type    | Description           | Valeurs possibles                                         | Contraintes   | Priorité |
| ----------------- | ------- | --------------------- | --------------------------------------------------------- | ------------- | -------- |
| id                | UUID    | Identifiant           | UUID                                                      | PK, unique    | MVP      |
| user_id           | UUID    | Utilisateur           | Référence User                                            | FK vers User  | MVP      |
| skill_id          | UUID    | Compétence            | Référence Skill                                           | FK vers Skill | MVP      |
| proficiency_level | Texte   | Niveau de maîtrise    | "learning", "basic", "intermediate", "advanced", "expert" | Enum          | MVP      |
| is_primary        | Booléen | Compétence principale | true/false                                                | Défaut: false | MVP      |
| created_at        | Date    | Date d'ajout          | ISO 8601                                                  | Automatique   | MVP      |



#### 🔹 Repository Lié (LinkedRepository)

| Nom         | Type       | Description                    | Valeurs possibles            | Contraintes     | Priorité |
| ----------- | ---------- | ------------------------------ | ---------------------------- | --------------- | -------- |
| id          | UUID       | Identifiant                    | UUID                         | PK, unique      | MVP      |
| project_id  | UUID       | Projet parent                  | Référence Project            | FK vers Project | MVP      |
| github_url  | Texte      | URL du repository              | URL GitHub                   | Obligatoire     | MVP      |
| name        | Texte      | Nom du repository              | Max 100 caractères           | Obligatoire     | MVP      |
| description | Texte      | Description du repo            | Max 500 caractères           | Optionnel       | MVP      |
| is_main     | Booléen    | Repository principal du projet | true/false                   | Défaut: false   | MVP      |
| language    | Texte      | Langage principal              | "JavaScript", "Python", etc. | Optionnel       | MVP      |
| stars_count | Entier     | Nombre d'étoiles               | ≥ 0                          | Synchronisé     | MVP      |
| last_sync   | Date/Heure | Dernière synchronisation       | ISO 8601                     | Automatique     | MVP      |

**📝 Note technique :**

- `Project.github_main_repo` reste obligatoire (repo principal)
- `LinkedRepository` avec `is_main = false` pour repos secondaires
- Évite la duplication et maintient la cohérence
