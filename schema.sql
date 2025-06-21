-- This script creates the database schema for the recommendation engine's data sources.
-- It is designed for PostgreSQL.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------
--          Core Tables
-- ---------------------------------

CREATE TABLE "USER" (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "username" VARCHAR(30) NOT NULL UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- Other user fields can be added here
);

CREATE TABLE "PROJECT" (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "title" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- Other project fields can be added here
);

CREATE TABLE "PROJECT_ROLE" (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "project_id" UUID NOT NULL,
    "title" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_project
        FOREIGN KEY("project_id") 
        REFERENCES "PROJECT"("id")
        ON DELETE CASCADE
);

-- ---------------------------------
--     "Strong Interest" Tables
-- ---------------------------------

CREATE TABLE "TEAM_MEMBER" (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "user_id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "joined_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user
        FOREIGN KEY("user_id") 
        REFERENCES "USER"("id")
        ON DELETE CASCADE,
    
    CONSTRAINT fk_project
        FOREIGN KEY("project_id") 
        REFERENCES "PROJECT"("id")
        ON DELETE CASCADE,

    UNIQUE ("user_id", "project_id") -- A user can only be a member of a project once
);

CREATE TABLE "CONTRIBUTION" (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "user_id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "submitted_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(200),
    "type" VARCHAR(50),

    CONSTRAINT fk_user
        FOREIGN KEY("user_id") 
        REFERENCES "USER"("id")
        ON DELETE CASCADE,
    
    CONSTRAINT fk_project
        FOREIGN KEY("project_id") 
        REFERENCES "PROJECT"("id")
        ON DELETE CASCADE
);

CREATE TABLE "APPLICATION" (
    "id" UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "user_id" UUID NOT NULL,
    "project_role_id" UUID NOT NULL,
    "applied_at" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(50) DEFAULT 'pending',

    CONSTRAINT fk_user
        FOREIGN KEY("user_id") 
        REFERENCES "USER"("id")
        ON DELETE CASCADE,
    
    CONSTRAINT fk_project_role
        FOREIGN KEY("project_role_id") 
        REFERENCES "PROJECT_ROLE"("id")
        ON DELETE CASCADE,

    UNIQUE ("user_id", "project_role_id") -- A user can only apply for a specific role once
);

-- Add indexes for performance on foreign key columns
CREATE INDEX idx_project_role_project_id ON "PROJECT_ROLE"("project_id");
CREATE INDEX idx_team_member_user_id ON "TEAM_MEMBER"("user_id");
CREATE INDEX idx_team_member_project_id ON "TEAM_MEMBER"("project_id");
CREATE INDEX idx_contribution_user_id ON "CONTRIBUTION"("user_id");
CREATE INDEX idx_contribution_project_id ON "CONTRIBUTION"("project_id");
CREATE INDEX idx_application_user_id ON "APPLICATION"("user_id");
CREATE INDEX idx_application_project_role_id ON "APPLICATION"("project_role_id"); 