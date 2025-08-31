# dbt Test Models Documentation

## Overview

The OST Data Engine uses dbt models to manage test data for integration testing. This approach provides version control, documentation, and data quality validation for test data.

## Test Models Structure

```
src/dbt/models/test/
├── schema.yml              # Documentation and data quality tests
├── test_users.sql          # Test users with different profiles
├── test_projects.sql       # Test projects with various technologies
└── test_similarities.sql   # Test similarity scores
```

## Model Details

### test_users.sql

Creates test users with different programming language profiles:

```sql
{{
  config(
    materialized='table',
    tags=['test', 'fixtures']
  )
}}

SELECT 
  '123e4567-e89b-12d3-a456-426614174000'::uuid as id,
  'test_user_1' as username,
  'user1@test.com' as email,
  'Python' as primary_language,
  'Data Science' as category,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174001'::uuid as id,
  'test_user_2' as username,
  'user2@test.com' as email,
  'JavaScript' as primary_language,
  'Web Development' as category,
  NOW() as created_at

UNION ALL

SELECT 
  '123e4567-e89b-12d3-a456-426614174002'::uuid as id,
  'test_user_3' as username,
  'user3@test.com' as email,
  'Go' as primary_language,
  'Backend Development' as category,
  NOW() as created_at
```

**Test Users Created:**
- **test_user_1**: Python developer (Data Science)
- **test_user_2**: JavaScript developer (Web Development)  
- **test_user_3**: Go developer (Backend Development)

### test_projects.sql

Creates test projects with various technologies:

```sql
{{
  config(
    materialized='table',
    tags=['test', 'fixtures']
  )
}}

SELECT 
  '123e4567-e89b-12d3-a456-426614174003'::uuid as id,
  'Python ML Project' as title,
  'Machine learning project in Python with scikit-learn and pandas' as description,
  'Python' as primary_language,
  'Data Science' as category,
  1500 as stargazers_count,
  NOW() as created_at

-- ... more projects
```

**Test Projects Created:**
- **Python ML Project**: Data Science project (1500 stars)
- **JavaScript Web App**: Web Development project (800 stars)
- **Go Microservice**: Backend Development project (1200 stars)
- **Data Science Tool**: Data Science project (2000 stars)
- **React Component Library**: Web Development project (950 stars)

### test_similarities.sql

Generates realistic similarity scores between users and projects:

```sql
{{
  config(
    materialized='table',
    tags=['test', 'fixtures']
  )
}}

WITH test_users AS (
  SELECT * FROM {{ ref('test_users') }}
),
test_projects AS (
  SELECT * FROM {{ ref('test_projects') }}
)

SELECT 
  u.id as user_id,
  p.id as project_id,
  -- Realistic similarity scores based on language and category matches
  CASE 
    WHEN u.primary_language = p.primary_language THEN 0.85 + (random() * 0.10)
    WHEN u.category = p.category THEN 0.70 + (random() * 0.15)
    ELSE 0.50 + (random() * 0.20)
  END as similarity_score,
  
  -- ... similarity components
  
  NOW() as created_at

FROM test_users u
CROSS JOIN test_projects p

-- Ensure we have exactly 5 recommendations per user
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY u.id 
  ORDER BY similarity_score DESC
) <= 5
```

**Similarity Logic:**
- **Language Match**: High similarity (0.85-0.95) when user and project share language
- **Category Match**: Medium similarity (0.70-0.85) when user and project share category
- **No Match**: Lower similarity (0.50-0.70) for unrelated projects
- **Top 5**: Exactly 5 recommendations per user (RECOMMENDATION_TOP_N)

## Data Quality Tests

### schema.yml

Defines data quality tests for all test models:

```yaml
version: 2

models:
  - name: test_users
    description: "Test users for integration tests with different profiles"
    columns:
      - name: id
        description: "Unique user identifier"
        tests:
          - not_null
          - unique
      - name: username
        description: "User username"
        tests:
          - not_null
          - unique
      - name: primary_language
        description: "User's primary programming language"
        tests:
          - not_null
          - accepted_values:
              values: ['Python', 'JavaScript', 'Go']
      # ... more tests
```

**Data Quality Tests:**
- **Uniqueness**: Ensure no duplicate IDs or usernames
- **Not null**: Required fields are populated
- **Accepted values**: Languages and categories are valid
- **Relationships**: Foreign key constraints are valid
- **Range checks**: Similarity scores are in [0, 1]

## Usage

### Local Development

```bash
# Run test models
cd src/dbt
poetry run dbt run --select tag:test --target dev

# Run data quality tests
poetry run dbt test --select tag:test --target dev

# View documentation
poetry run dbt docs generate
poetry run dbt docs serve
```

### CI/CD

```bash
# Run test models in CI
cd src/dbt
poetry run dbt run --select tag:test --target ci

# Run tests in CI
poetry run dbt test --select tag:test --target ci
```

### Helper Script

```bash
# Use the helper script
python scripts/setup_test_data_fallback.py
```

## Configuration

### dbt Profiles

The test models use different profiles for different environments:

```yaml
# profiles.yml
ost_transform:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DB_HOST') }}"
      user: "{{ env_var('POSTGRES_USER') }}"
      password: "{{ env_var('POSTGRES_PASSWORD') }}"
      port: "{{ env_var('DB_PORT') | as_native }}"
      dbname: "{{ env_var('POSTGRES_DB') }}"
      schema: "{{ env_var('DB_SCHEMA') }}"
      threads: "{{ env_var('DB_THREADS') | as_native }}"
    
    ci:
      type: postgres
      host: "{{ env_var('POSTGRES_HOST') }}"
      user: "{{ env_var('POSTGRES_USER') }}"
      password: "{{ env_var('POSTGRES_PASSWORD') }}"
      port: "{{ env_var('POSTGRES_PORT') | as_native }}"
      dbname: "{{ env_var('POSTGRES_DB') }}"
      schema: "public"
      threads: 1
```

### Environment Variables

Required environment variables for test models:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_PORT=5434
POSTGRES_DB=OST_PROD

# dbt
DBT_PROJECT_DIR=src/dbt
```

## Fallback Mechanism

If dbt fails in CI, a fallback script creates test data directly:

```bash
# Fallback script
python scripts/setup_test_data_fallback.py
```

This script:
- Creates the same test data structure
- Uses direct SQL instead of dbt
- Ensures tests can run even if dbt is unavailable
- Maintains data consistency

## Best Practices

### 1. Version Control
- All test data is versioned with Git
- Changes to test data are tracked
- Test data can be rolled back if needed

### 2. Documentation
- All models have clear descriptions
- Column descriptions explain purpose
- Data quality tests document expectations

### 3. Data Quality
- Comprehensive validation tests
- Realistic data relationships
- Consistent data across environments

### 4. Maintainability
- Easy to add new test users/projects
- Simple to modify similarity logic
- Clear separation of concerns

## Troubleshooting

### Common Issues

1. **dbt Model Not Found**
   ```bash
   # Check model exists
   ls src/dbt/models/test/
   
   # Check dbt project configuration
   cat src/dbt/dbt_project.yml
   ```

2. **Database Connection Failed**
   ```bash
   # Test connection
   psql $DATABASE_URL -c "SELECT 1;"
   
   # Check environment variables
   echo $POSTGRES_HOST
   echo $POSTGRES_USER
   ```

3. **Data Quality Tests Failed**
   ```bash
   # Run specific test
   poetry run dbt test --select test_name --target dev
   
   # Check data
   psql $DATABASE_URL -c "SELECT * FROM test_users;"
   ```

### Debug Commands

```bash
# Debug dbt configuration
poetry run dbt debug --target dev

# Run with verbose output
poetry run dbt run --select tag:test --target dev --debug

# Check model dependencies
poetry run dbt list --select tag:test
```
