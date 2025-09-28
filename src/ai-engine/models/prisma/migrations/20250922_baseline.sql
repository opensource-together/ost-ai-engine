-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "staging";

-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- CreateEnum
CREATE TYPE "public"."TechStackType" AS ENUM ('TECH', 'LANGUAGE');

-- CreateEnum
CREATE TYPE "public"."Platform" AS ENUM ('GITHUB', 'GITLAB');

-- CreateTable
CREATE TABLE "public"."Skeleton" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "name" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "myAttribute" TEXT,

    CONSTRAINT "Skeleton_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."user" (
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "emailVerified" BOOLEAN NOT NULL DEFAULT false,
    "image" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "bio" TEXT,
    "jobTitle" TEXT,
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "discordUrl" TEXT,
    "githubUrl" TEXT,
    "linkedinUrl" TEXT,
    "twitterUrl" TEXT,
    "websiteUrl" TEXT,

    CONSTRAINT "user_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."session" (
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "token" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "ipAddress" TEXT,
    "userAgent" TEXT,
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "userId" UUID NOT NULL,

    CONSTRAINT "session_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."account" (
    "accountId" TEXT NOT NULL,
    "providerId" TEXT NOT NULL,
    "accessToken" TEXT,
    "refreshToken" TEXT,
    "idToken" TEXT,
    "accessTokenExpiresAt" TIMESTAMP(3),
    "refreshTokenExpiresAt" TIMESTAMP(3),
    "scope" TEXT,
    "password" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "userId" UUID NOT NULL,

    CONSTRAINT "account_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."verification" (
    "identifier" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),

    CONSTRAINT "verification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."tech_stack" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "name" TEXT NOT NULL,
    "iconUrl" TEXT NOT NULL,
    "type" "public"."TechStackType" NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tech_stack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."user_tech_stack" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "userId" UUID NOT NULL,
    "techStackId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_tech_stack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."trending_projects" (
    "uuid" UUID NOT NULL,
    "platform" TEXT,
    "externalid" TEXT,
    "name" TEXT,
    "fullname" TEXT,
    "description" TEXT,
    "htmlurl" TEXT,
    "homepage" TEXT,
    "defaultbranch" TEXT,
    "visibility" TEXT,
    "language" TEXT,
    "topics" JSONB,
    "license" TEXT,
    "stars" INTEGER,
    "forks" INTEGER,
    "openissues" INTEGER,
    "subscribers" INTEGER,
    "archived" BOOLEAN,
    "owner" TEXT,
    "namespace" TEXT,
    "createdatsource" TIMESTAMPTZ(6),
    "updatedatsource" TIMESTAMPTZ(6),
    "lastactivityatsource" TIMESTAMPTZ(6),

    CONSTRAINT "trending_projects_pkey" PRIMARY KEY ("uuid")
);

-- CreateTable
CREATE TABLE "staging"."stg_trending_projects" (
    "platform" TEXT,
    "external_id" TEXT,
    "name" TEXT,
    "full_name" TEXT,
    "description" TEXT,
    "html_url" TEXT,
    "homepage" TEXT,
    "default_branch" TEXT,
    "visibility" TEXT,
    "language" TEXT,
    "topics" JSONB,
    "license" TEXT,
    "stars" INTEGER,
    "forks" INTEGER,
    "open_issues" INTEGER,
    "subscribers" INTEGER,
    "archived" BOOLEAN DEFAULT false,
    "owner" TEXT,
    "namespace" TEXT,
    "created_at_source" TIMESTAMPTZ(6),
    "updated_at_source" TIMESTAMPTZ(6),
    "last_activity_at_source" TIMESTAMPTZ(6),
    "_loaded_at" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,
    "uuid" UUID NOT NULL DEFAULT gen_random_uuid(),

    CONSTRAINT "stg_trending_projects_pkey" PRIMARY KEY ("uuid")
);

-- CreateTable
CREATE TABLE "staging"."stg_trending_project" (
    "id" UUID,
    "platform" TEXT,
    "external_id" TEXT,
    "name" TEXT,
    "full_name" TEXT,
    "description" TEXT,
    "html_url" TEXT,
    "homepage" TEXT,
    "default_branch" TEXT,
    "visibility" TEXT,
    "language" TEXT,
    "topics" JSONB,
    "license" TEXT,
    "stars" INTEGER,
    "forks" INTEGER,
    "open_issues" INTEGER,
    "subscribers" INTEGER,
    "archived" BOOLEAN,
    "owner" TEXT,
    "namespace" TEXT,
    "created_at_source" TIMESTAMPTZ(6),
    "updated_at_source" TIMESTAMPTZ(6),
    "last_activity_at_source" TIMESTAMPTZ(6),
    "_loaded_at" TIMESTAMPTZ(6)
);

-- CreateIndex
CREATE UNIQUE INDEX "user_email_key" ON "public"."user"("email");

-- CreateIndex
CREATE UNIQUE INDEX "session_token_key" ON "public"."session"("token");

-- CreateIndex
CREATE UNIQUE INDEX "tech_stack_name_key" ON "public"."tech_stack"("name");

-- CreateIndex
CREATE UNIQUE INDEX "user_tech_stack_userId_techStackId_key" ON "public"."user_tech_stack"("userId", "techStackId");

-- CreateIndex
CREATE INDEX "stg_trending_projects_pk_idx" ON "staging"."stg_trending_projects"("platform", "external_id");

-- CreateIndex
CREATE UNIQUE INDEX "stg_trending_projects_platform_external_id_key" ON "staging"."stg_trending_projects"("platform", "external_id");

-- AddForeignKey
ALTER TABLE "public"."session" ADD CONSTRAINT "session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."account" ADD CONSTRAINT "account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."user_tech_stack" ADD CONSTRAINT "user_tech_stack_techStackId_fkey" FOREIGN KEY ("techStackId") REFERENCES "public"."tech_stack"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."user_tech_stack" ADD CONSTRAINT "user_tech_stack_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."trending_projects" ADD CONSTRAINT "trending_projects_uuid_fkey" FOREIGN KEY ("uuid") REFERENCES "staging"."stg_trending_projects"("uuid") ON DELETE NO ACTION ON UPDATE CASCADE;

