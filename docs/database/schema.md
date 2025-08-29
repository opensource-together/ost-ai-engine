# Database Schema Documentation

## Overview

The OST Data Engine uses PostgreSQL with the pgvector extension for efficient vector storage and similarity search operations.

## Core Tables

### User Management

#### USER
```sql
CREATE TABLE "USER" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    login VARCHAR(100),
    avatar_url TEXT,
    location VARCHAR(100),
    company VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### USER_GITHUB_CREDENTIALS
```sql
CREATE TABLE "USER_GITHUB_CREDENTIALS" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES "USER"(id),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Project Management

#### PROJECT
```sql
CREATE TABLE "PROJECT" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(150) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    short_description TEXT,
    readme TEXT,
    primary_language VARCHAR(50),
    homepage_url TEXT,
    license VARCHAR(100),
    stargazers_count INTEGER DEFAULT 0 NOT NULL,
    watchers_count INTEGER DEFAULT 0 NOT NULL,
    forks_count INTEGER DEFAULT 0 NOT NULL,
    open_issues_count INTEGER DEFAULT 0 NOT NULL,
    is_fork BOOLEAN DEFAULT FALSE NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE NOT NULL,
    topics TEXT[],
    languages JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    pushed_at TIMESTAMP WITH TIME ZONE,
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    image TEXT,
    cover_images TEXT,
    author_id UUID REFERENCES "USER"(id),
    owner_id UUID REFERENCES "USER"(id),
    owner_login VARCHAR(39)
);
```

### Categories and Tech Stacks

#### CATEGORY
```sql
CREATE TABLE "CATEGORY" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### TECH_STACK
```sql
CREATE TABLE "TECH_STACK" (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    icon_url TEXT,
    type VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Association Tables

#### PROJECT_CATEGORY
```sql
CREATE TABLE "PROJECT_CATEGORY" (
    project_id UUID REFERENCES "PROJECT"(id),
    category_id UUID REFERENCES "CATEGORY"(id),
    PRIMARY KEY (project_id, category_id)
);
```

#### PROJECT_TECH_STACK
```sql
CREATE TABLE "PROJECT_TECH_STACK" (
    project_id UUID REFERENCES "PROJECT"(id),
    tech_stack_id UUID REFERENCES "TECH_STACK"(id),
    PRIMARY KEY (project_id, tech_stack_id)
);
```

#### USER_CATEGORY
```sql
CREATE TABLE "USER_CATEGORY" (
    user_id UUID REFERENCES "USER"(id),
    category_id UUID REFERENCES "CATEGORY"(id),
    PRIMARY KEY (user_id, category_id)
);
```

#### USER_TECH_STACK
```sql
CREATE TABLE "USER_TECH_STACK" (
    user_id UUID REFERENCES "USER"(id),
    tech_stack_id UUID REFERENCES "TECH_STACK"(id),
    PRIMARY KEY (user_id, tech_stack_id)
);
```

## Machine Learning Tables

### Embeddings

#### embed_PROJECTS
```sql
CREATE TABLE "embed_PROJECTS" (
    project_id UUID REFERENCES "PROJECT"(id) PRIMARY KEY,
    embedding_text TEXT NOT NULL,
    embedding_vector vector(384),
    last_ingested_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### embed_USERS
```sql
CREATE TABLE "embed_USERS" (
    user_id UUID REFERENCES "USER"(id) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    embedding_text TEXT NOT NULL,
    embedding_vector vector(384),
    bio TEXT,
    categories TEXT[],
    last_ingested_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### hybrid_PROJECT_embeddings
```sql
CREATE TABLE "hybrid_PROJECT_embeddings" (
    project_id UUID REFERENCES "PROJECT"(id) PRIMARY KEY,
    semantic_embedding vector(384),
    structured_features JSONB,
    hybrid_vector vector(422),
    similarity_weights JSONB,
    last_ingested_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Similarity Storage

#### USER_PROJECT_SIMILARITY
```sql
CREATE TABLE "USER_PROJECT_SIMILARITY" (
    user_id UUID REFERENCES "USER"(id),
    project_id UUID REFERENCES "PROJECT"(id),
    similarity_score FLOAT NOT NULL,
    semantic_similarity FLOAT,
    category_similarity FLOAT,
    language_similarity FLOAT,
    popularity_similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);
```

## Indexes

### Performance Indexes

```sql
-- User indexes
CREATE INDEX idx_user_username ON "USER"(username);
CREATE INDEX idx_user_email ON "USER"(email);

-- Project indexes
CREATE INDEX idx_project_full_name ON "PROJECT"(full_name);
CREATE INDEX idx_project_primary_language ON "PROJECT"(primary_language);
CREATE INDEX idx_project_stargazers_count ON "PROJECT"(stargazers_count);

-- Embedding indexes
CREATE INDEX idx_embed_projects_vector ON "embed_PROJECTS" USING ivfflat (embedding_vector vector_cosine_ops);
CREATE INDEX idx_embed_users_vector ON "embed_USERS" USING ivfflat (embedding_vector vector_cosine_ops);
CREATE INDEX idx_hybrid_projects_vector ON "hybrid_PROJECT_embeddings" USING ivfflat (hybrid_vector vector_cosine_ops);

-- Similarity indexes
CREATE INDEX idx_user_project_similarity_score ON "USER_PROJECT_SIMILARITY" (user_id, similarity_score);
CREATE INDEX idx_user_project_similarity_user ON "USER_PROJECT_SIMILARITY" (user_id);
CREATE INDEX idx_user_project_similarity_project ON "USER_PROJECT_SIMILARITY" (project_id);
```

## Extensions

### Required Extensions

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable JSON operations
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

## Data Types

### Vector Types
- `vector(384)`: 384-dimensional vectors for semantic embeddings
- `vector(422)`: 422-dimensional hybrid vectors

### Array Types
- `TEXT[]`: Array of text values (categories, tech stacks)
- `JSONB`: JSON binary format for structured data

### UUID Types
- `UUID`: Universally unique identifiers for all primary keys

## Constraints

### Foreign Key Constraints
All association tables maintain referential integrity with their parent tables.

### Unique Constraints
- Username and email must be unique in USER table
- Project full_name must be unique in PROJECT table
- Category and tech stack names must be unique

### Not Null Constraints
- Critical fields like username, email, project title are NOT NULL
- Similarity scores in USER_PROJECT_SIMILARITY are NOT NULL

## Data Integrity

### Triggers
```sql
-- Auto-update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "USER"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Validation
- Email format validation
- URL format validation
- Vector dimension validation
- Similarity score range validation (0-1)
