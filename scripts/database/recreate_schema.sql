-- =============================================================================
-- 🗄️ DATABASE SCHEMA RECREATION SCRIPT
-- =============================================================================
-- This script recreates the complete database schema for the OST data engine
-- Run this to reset the database to a clean state
-- =============================================================================

-- Drop all tables in reverse dependency order
DROP TABLE IF EXISTS "hybrid_PROJECT_embeddings" CASCADE;
DROP TABLE IF EXISTS "embed_PROJECTS" CASCADE;
DROP TABLE IF EXISTS "embed_USERS" CASCADE;
DROP TABLE IF EXISTS "USER_PROJECT_SIMILARITY" CASCADE;
DROP TABLE IF EXISTS "PROJECT_SIMILARITY" CASCADE;
DROP TABLE IF EXISTS "USER_SIMILARITY" CASCADE;
DROP TABLE IF EXISTS "PROJECT_ROLE_APPLICATION_PROJECT_GOAL" CASCADE;
DROP TABLE IF EXISTS "PROJECT_ROLE_APPLICATION" CASCADE;
DROP TABLE IF EXISTS "PROJECT_GOAL" CASCADE;
DROP TABLE IF EXISTS "PROJECT_ROLE" CASCADE;
DROP TABLE IF EXISTS "PROJECT_TECH_STACK" CASCADE;
DROP TABLE IF EXISTS "PROJECT_CATEGORY" CASCADE;
DROP TABLE IF EXISTS "USER_CATEGORY" CASCADE;
DROP TABLE IF EXISTS "USER_TECH_STACK" CASCADE;
DROP TABLE IF EXISTS "TECH_STACK" CASCADE;
DROP TABLE IF EXISTS "CATEGORY" CASCADE;
DROP TABLE IF EXISTS "PROJECT" CASCADE;
DROP TABLE IF EXISTS "USER" CASCADE;
DROP TABLE IF EXISTS "github_PROJECT" CASCADE;

-- =============================================================================
-- 📊 CORE ENTITIES
-- =============================================================================

-- Users table
CREATE TABLE "USER" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    login VARCHAR(100),
    avatar_url TEXT,
    location VARCHAR(100),
    company VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table (transformed from GitHub data)
CREATE TABLE "PROJECT" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(150) UNIQUE NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    short_description TEXT,
    readme TEXT,
    primary_language VARCHAR(50),
    homepage_url TEXT,
    license VARCHAR(100),
    stargazers_count INTEGER DEFAULT 0,
    watchers_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    is_fork BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_disabled BOOLEAN DEFAULT FALSE,
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

-- =============================================================================
-- 🏷️ REFERENCE TABLES
-- =============================================================================

-- Categories table
CREATE TABLE "CATEGORY" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tech Stack table
CREATE TABLE "TECH_STACK" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    icon_url TEXT,
    type VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 🔗 RELATIONSHIP TABLES
-- =============================================================================

-- User-Category relationships
CREATE TABLE "USER_CATEGORY" (
    user_id UUID REFERENCES "USER"(id) ON DELETE CASCADE,
    category_id UUID REFERENCES "CATEGORY"(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, category_id)
);

-- User-Tech Stack relationships
CREATE TABLE "USER_TECH_STACK" (
    user_id UUID REFERENCES "USER"(id) ON DELETE CASCADE,
    tech_stack_id UUID REFERENCES "TECH_STACK"(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, tech_stack_id)
);

-- Project-Category relationships
CREATE TABLE "PROJECT_CATEGORY" (
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    category_id UUID REFERENCES "CATEGORY"(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, category_id)
);

-- Project-Tech Stack relationships
CREATE TABLE "PROJECT_TECH_STACK" (
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    tech_stack_id UUID REFERENCES "TECH_STACK"(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, tech_stack_id)
);

-- =============================================================================
-- 🎯 PROJECT MANAGEMENT
-- =============================================================================

-- Project Roles table
CREATE TABLE "PROJECT_ROLE" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    is_filled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project Goals table
CREATE TABLE "PROJECT_GOAL" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    goal VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project Role Applications table
CREATE TABLE "PROJECT_ROLE_APPLICATION" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    project_title VARCHAR(100),
    project_role_id UUID REFERENCES "PROJECT_ROLE"(id) ON DELETE CASCADE,
    project_role_title VARCHAR(100),
    project_description TEXT,
    user_id UUID REFERENCES "USER"(id) ON DELETE CASCADE,
    status VARCHAR(20),
    motivation_letter TEXT,
    rejection_reason TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project External Links table
CREATE TABLE "PROJECT_EXTERNAL_LINK" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    type VARCHAR(50),
    url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team Members table
CREATE TABLE "TEAM_MEMBER" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "USER"(id) ON DELETE CASCADE,
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User GitHub Credentials table
CREATE TABLE "USER_GITHUB_CREDENTIALS" (
    user_id UUID PRIMARY KEY REFERENCES "USER"(id) ON DELETE CASCADE,
    github_access_token TEXT,
    github_user_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Social Links table
CREATE TABLE "USER_SOCIAL_LINK" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "USER"(id) ON DELETE CASCADE,
    type VARCHAR(50),
    url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, type)
);

-- Key Features table
CREATE TABLE "KEY_FEATURE" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    feature VARCHAR(200) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 🧠 MACHINE LEARNING TABLES
-- =============================================================================

-- Raw GitHub data staging table
CREATE TABLE "github_PROJECT" (
    full_name VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255) NOT NULL,
    description TEXT,
    fork BOOLEAN DEFAULT FALSE,
    language VARCHAR(100),
    stargazers_count INTEGER DEFAULT 0,
    watchers_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    topics JSONB,
    archived BOOLEAN DEFAULT FALSE,
    disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    pushed_at TIMESTAMP WITH TIME ZONE,
    homepage TEXT,
    license VARCHAR(255),
    languages_map JSONB,
    readme TEXT,
    raw JSONB,
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Semantic embeddings table for projects
CREATE TABLE "embed_PROJECTS" (
    project_id UUID PRIMARY KEY REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    embedding_text TEXT NOT NULL,
    embedding_vector vector(384),
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hybrid embeddings table for projects (NEW!)
CREATE TABLE "hybrid_PROJECT_embeddings" (
    project_id UUID PRIMARY KEY REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    semantic_embedding vector(384),
    structured_features JSONB,
    hybrid_vector vector(422),
    similarity_weights JSONB,
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User embeddings table
CREATE TABLE "embed_USERS" (
    user_id UUID PRIMARY KEY REFERENCES "USER"(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    embedding_text TEXT NOT NULL,
    embedding_vector vector(384),
    bio TEXT,
    categories TEXT[],
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 🔗 RELATIONSHIP TABLES (after main tables)
-- =============================================================================

-- Project Role Application - Project Goal relationships
CREATE TABLE "PROJECT_ROLE_APPLICATION_PROJECT_GOAL" (
    application_id UUID REFERENCES "PROJECT_ROLE_APPLICATION"(id) ON DELETE CASCADE,
    project_goal_id UUID REFERENCES "PROJECT_GOAL"(id) ON DELETE CASCADE,
    PRIMARY KEY (application_id, project_goal_id)
);

-- Project Role Application - Key Feature relationships
CREATE TABLE "PROJECT_ROLE_APPLICATION_KEY_FEATURE" (
    application_id UUID REFERENCES "PROJECT_ROLE_APPLICATION"(id) ON DELETE CASCADE,
    key_feature_id UUID REFERENCES "KEY_FEATURE"(id) ON DELETE CASCADE,
    PRIMARY KEY (application_id, key_feature_id)
);

-- Team Member - Project Role relationships
CREATE TABLE "TEAM_MEMBER_PROJECT_ROLE" (
    team_member_id UUID REFERENCES "TEAM_MEMBER"(id) ON DELETE CASCADE,
    project_role_id UUID REFERENCES "PROJECT_ROLE"(id) ON DELETE CASCADE,
    PRIMARY KEY (team_member_id, project_role_id)
);

-- Project Role - Tech Stack relationships
CREATE TABLE "PROJECT_ROLE_TECH_STACK" (
    project_role_id UUID REFERENCES "PROJECT_ROLE"(id) ON DELETE CASCADE,
    tech_stack_id UUID REFERENCES "TECH_STACK"(id) ON DELETE CASCADE,
    PRIMARY KEY (project_role_id, tech_stack_id)
);

-- =============================================================================
-- 📈 SIMILARITY MATRICES
-- =============================================================================

-- User-Project similarity matrix (MAIN FOCUS - only one we need!)

-- User-Project similarity matrix (MAIN FOCUS)
CREATE TABLE "USER_PROJECT_SIMILARITY" (
    user_id UUID REFERENCES "USER"(id) ON DELETE CASCADE,
    project_id UUID REFERENCES "PROJECT"(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    semantic_similarity FLOAT,
    category_similarity FLOAT,
    language_similarity FLOAT,
    popularity_similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);

-- =============================================================================
-- 📊 INDEXES FOR PERFORMANCE
-- =============================================================================

-- Core indexes
CREATE INDEX idx_user_username ON "USER"(username);
CREATE INDEX idx_user_email ON "USER"(email);
CREATE INDEX idx_project_full_name ON "PROJECT"(full_name);
CREATE INDEX idx_project_title ON "PROJECT"(title);
CREATE INDEX idx_category_name ON "CATEGORY"(name);
CREATE INDEX idx_tech_stack_name ON "TECH_STACK"(name);

-- Relationship indexes
CREATE INDEX idx_user_category_user_id ON "USER_CATEGORY"(user_id);
CREATE INDEX idx_user_category_category_id ON "USER_CATEGORY"(category_id);
CREATE INDEX idx_user_tech_stack_user_id ON "USER_TECH_STACK"(user_id);
CREATE INDEX idx_user_tech_stack_tech_stack_id ON "USER_TECH_STACK"(tech_stack_id);
CREATE INDEX idx_project_category_project_id ON "PROJECT_CATEGORY"(project_id);
CREATE INDEX idx_project_category_category_id ON "PROJECT_CATEGORY"(category_id);
CREATE INDEX idx_project_tech_stack_project_id ON "PROJECT_TECH_STACK"(project_id);
CREATE INDEX idx_project_tech_stack_tech_stack_id ON "PROJECT_TECH_STACK"(tech_stack_id);

-- ML indexes
CREATE INDEX idx_embed_projects_project_id ON "embed_PROJECTS"(project_id);
CREATE INDEX idx_hybrid_project_embeddings_project_id ON "hybrid_PROJECT_embeddings"(project_id);
CREATE INDEX idx_embed_users_user_id ON "embed_USERS"(user_id);

-- Additional indexes for new tables
CREATE INDEX idx_project_external_link_project_id ON "PROJECT_EXTERNAL_LINK"(project_id);
CREATE INDEX idx_team_member_user_id ON "TEAM_MEMBER"(user_id);
CREATE INDEX idx_team_member_project_id ON "TEAM_MEMBER"(project_id);
CREATE INDEX idx_user_social_link_user_id ON "USER_SOCIAL_LINK"(user_id);
CREATE INDEX idx_key_feature_project_id ON "KEY_FEATURE"(project_id);
CREATE INDEX idx_project_role_application_project_id ON "PROJECT_ROLE_APPLICATION"(project_id);
CREATE INDEX idx_project_role_application_user_id ON "PROJECT_ROLE_APPLICATION"(user_id);

-- Similarity indexes (only for USER_PROJECT_SIMILARITY)
CREATE INDEX idx_user_project_similarity_user ON "USER_PROJECT_SIMILARITY"(user_id);
CREATE INDEX idx_user_project_similarity_project ON "USER_PROJECT_SIMILARITY"(project_id);
CREATE INDEX idx_user_project_similarity_score ON "USER_PROJECT_SIMILARITY"(similarity_score DESC);

-- =============================================================================
-- ✅ SCHEMA CREATION COMPLETE
-- =============================================================================

-- Insert some default categories
INSERT INTO "CATEGORY" (name) VALUES
('IA & Machine Learning'),
('Applications Mobile'),
('Applications Web'),
('Blockchain & Crypto'),
('Data & Analytics'),
('DevOps & Infrastructure'),
('Gaming'),
('Security'),
('Open Source'),
('Education');

-- Insert some default tech stacks
INSERT INTO "TECH_STACK" (name, icon_url, type) VALUES
('JavaScript', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg', 'LANGUAGE'),
('TypeScript', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/typescript/typescript-original.svg', 'LANGUAGE'),
('Python', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg', 'LANGUAGE'),
('Go', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/go/go-original.svg', 'LANGUAGE'),
('Java', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/java/java-original.svg', 'LANGUAGE'),
('Rust', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/rust/rust-plain.svg', 'LANGUAGE'),
('React', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/react/react-original.svg', 'TECH'),
('Vue.js', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vuejs/vuejs-original.svg', 'TECH'),
('Node.js', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nodejs/nodejs-original.svg', 'TECH'),
('Django', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/django/django-plain.svg', 'TECH'),
('FastAPI', 'https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png', 'TECH'),
('PostgreSQL', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg', 'TECH'),
('MongoDB', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mongodb/mongodb-original.svg', 'TECH'),
('Docker', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg', 'TECH'),
('Kubernetes', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/kubernetes/kubernetes-plain.svg', 'TECH'),
('AWS', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/amazonwebservices/amazonwebservices-original.svg', 'TECH'),
('TensorFlow', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/tensorflow/tensorflow-original.svg', 'TECH'),
('PyTorch', 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/pytorch/pytorch-original.svg', 'TECH');

COMMIT;
