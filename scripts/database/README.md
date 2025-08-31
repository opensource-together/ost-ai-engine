# 📁 Database Scripts

This directory contains essential scripts for database management.

## 🗂️ Structure

```
scripts/
├── database/
│   ├── clean_tables.sql          # Clean operational tables
│   ├── create_test_users.py      # Create test users
│   ├── recreate_schema.sql       # Recreate complete schema (SQL)
    └── README.md                 # This documentation
```

## 📋 Available Scripts

### **🗑️ `clean_tables.sql`**
**Usage:** `psql -d OST_PROD -f scripts/database/clean_tables.sql`

**Description:** Cleans all operational tables while preserving reference tables (`CATEGORY`, `TECH_STACK`).

**Cleaned tables:**
- `github_PROJECT`, `USER`, `PROJECT`
- `USER_CATEGORY`, `USER_TECH_STACK`
- `PROJECT_CATEGORY`, `PROJECT_TECH_STACK`
- `embed_PROJECTS`, `embed_USERS`
- And all other operational tables

### **👥 `create_test_users.py`**
**Usage:** `python scripts/database/create_test_users.py`

**Description:** Creates 10 test users with realistic profiles and automatically maps them to categories and tech stacks.

**Created users:**
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

### **🏗️ `recreate_schema.sql`** ⭐ **RECOMMENDED**
**Usage:** `psql -d OST_PROD -f scripts/database/recreate_schema.sql`

**Description:** Complete SQL script to recreate the entire database schema.

**Advantages:**
- ✅ **Faster:** Direct SQL execution
- ✅ **More complete:** Includes all ML tables
- ✅ **Reference data:** Inserts categories and tech stacks
- ✅ **Safety:** Automatic production environment check
- ✅ **Maintenance:** Explicit definition of each table

**Includes:**
- All main tables
- Reference tables (`CATEGORY`, `TECH_STACK`)
- Relationship tables
- ML tables (`embed_PROJECTS`, `embed_USERS`, `hybrid_PROJECT_embeddings`)
- Performance indexes
- Default reference data

## 🔄 Typical Workflow

### **1. Complete database reset**
```bash
# ✅ RECOMMENDED: Via SQL (faster and more complete)
psql -d OST_PROD -f scripts/database/recreate_schema.sql
```

### **2. Clean data**
```bash
psql -d OST_PROD -f scripts/database/clean_tables.sql
```

### **3. Create test data**
```bash
python scripts/database/create_test_users.py
```

### **4. Run Dagster pipeline**
```bash
export DAGSTER_HOME=$(pwd)/logs/dagster
poetry run dagster job execute -j training_data_pipeline
```

## ⚠️ Important Notes

- **Backup:** Always backup before recreating the schema
- **Production:** The SQL script automatically checks the environment
- **Dependencies:** Python scripts require project dependencies
- **Environment variables:** Make sure `.env` is configured

## 🗑️ Removed Scripts

The following scripts have been removed as their functionality is now integrated into the Dagster pipeline:

- `recreate_schema.py` → **Replaced by `recreate_schema.sql`** (more complete and faster)
- `test_user_recommendations.py` → Replaced by `test_single_user_evaluation.py`
- `test_user_project_similarity.py` → Integrated into Dagster pipeline
- `create_user_category_table.sql` → Included in `recreate_schema.sql`
- `map_projects_to_references.py` → Integrated into `reference_assets.py`
- `populate_reference_tables.py` → Integrated into `reference_assets.py`
