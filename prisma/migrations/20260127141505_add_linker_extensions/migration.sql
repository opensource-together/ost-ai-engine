/*
  Warnings:

  - You are about to drop the `verification` table. If the table is not empty, all the data it contains will be lost.

*/
-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "github";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "match";

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "ml";

-- CreateExtension
CREATE EXTENSION IF NOT EXISTS "vector";

-- DropTable
DROP TABLE "verification";

-- CreateTable
CREATE TABLE "public"."verification_token" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "identifier" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "verification_token_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."project_embedding" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "project_embedding_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "match"."project_classification" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "categoryId" UUID,
    "domainId" UUID,
    "categoryConfidence" DOUBLE PRECISION,
    "domainConfidence" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "project_classification_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "github"."raw_github_readme" (
    "id" UUID NOT NULL,
    "project_id" TEXT NOT NULL,
    "repo_url" TEXT,
    "content" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "raw_github_readme_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "github"."raw_github_topics" (
    "id" UUID NOT NULL,
    "project_id" TEXT NOT NULL,
    "repo_url" TEXT,
    "topics" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "raw_github_topics_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "github"."raw_github_languages" (
    "id" UUID NOT NULL,
    "project_id" TEXT NOT NULL,
    "repo_url" TEXT,
    "languages" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "raw_github_languages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "github"."raw_github_project" (
    "id" UUID NOT NULL,
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "raw_github_project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "github"."int_github_detection" (
    "id" TEXT NOT NULL,
    "project_id" TEXT NOT NULL,
    "repo_url" TEXT,
    "language_detected" TEXT,
    "language_confidence" DOUBLE PRECISION,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "int_github_detection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ml"."embd_github_project" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "vector" vector,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "embd_github_project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ml"."embd_user" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "userId" UUID NOT NULL,
    "vector" vector,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "embd_user_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "project_classification_projectId_key" ON "match"."project_classification"("projectId");

-- CreateIndex
CREATE UNIQUE INDEX "int_github_detection_project_id_key" ON "github"."int_github_detection"("project_id");

-- CreateIndex
CREATE UNIQUE INDEX "embd_github_project_projectId_key" ON "ml"."embd_github_project"("projectId");

-- CreateIndex
CREATE UNIQUE INDEX "embd_user_userId_key" ON "ml"."embd_user"("userId");

-- AddForeignKey
ALTER TABLE "public"."project_embedding" ADD CONSTRAINT "project_embedding_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "public"."Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match"."project_classification" ADD CONSTRAINT "project_classification_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "public"."Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match"."project_classification" ADD CONSTRAINT "project_classification_categoryId_fkey" FOREIGN KEY ("categoryId") REFERENCES "public"."Category"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match"."project_classification" ADD CONSTRAINT "project_classification_domainId_fkey" FOREIGN KEY ("domainId") REFERENCES "public"."Domain"("id") ON DELETE SET NULL ON UPDATE CASCADE;
