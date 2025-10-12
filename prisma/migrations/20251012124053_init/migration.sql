/*
  Warnings:

  - A unique constraint covering the columns `[githubUsername]` on the table `user` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[gitlabUsername]` on the table `user` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[githubId]` on the table `user` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[gitlabId]` on the table `user` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateEnum
CREATE TYPE "Provider" AS ENUM ('GITHUB', 'GITLAB');

-- AlterTable
ALTER TABLE "user" ADD COLUMN     "githubId" TEXT,
ADD COLUMN     "githubUsername" TEXT,
ADD COLUMN     "gitlabId" TEXT,
ADD COLUMN     "gitlabUrl" TEXT,
ADD COLUMN     "gitlabUsername" TEXT;

-- CreateTable
CREATE TABLE "project_tech_stack" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "techStackId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "project_tech_stack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Category" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Category_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "project_category" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "categoryId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "project_category_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Project" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "title" TEXT NOT NULL,
    "description" TEXT,
    "repoUrl" TEXT,
    "provider" "Provider" NOT NULL,
    "githubUrl" TEXT,
    "gitlabUrl" TEXT,
    "twitterUrl" TEXT,
    "linkedinUrl" TEXT,
    "discordUrl" TEXT,
    "websiteUrl" TEXT,
    "published" BOOLEAN NOT NULL DEFAULT false,
    "ownerId" UUID,
    "logoUrl" TEXT,
    "imagesUrls" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "project_tech_stack_projectId_techStackId_key" ON "project_tech_stack"("projectId", "techStackId");

-- CreateIndex
CREATE UNIQUE INDEX "Category_name_key" ON "Category"("name");

-- CreateIndex
CREATE UNIQUE INDEX "project_category_projectId_categoryId_key" ON "project_category"("projectId", "categoryId");

-- CreateIndex
CREATE UNIQUE INDEX "user_githubUsername_key" ON "user"("githubUsername");

-- CreateIndex
CREATE UNIQUE INDEX "user_gitlabUsername_key" ON "user"("gitlabUsername");

-- CreateIndex
CREATE UNIQUE INDEX "user_githubId_key" ON "user"("githubId");

-- CreateIndex
CREATE UNIQUE INDEX "user_gitlabId_key" ON "user"("gitlabId");

-- AddForeignKey
ALTER TABLE "project_tech_stack" ADD CONSTRAINT "project_tech_stack_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project_tech_stack" ADD CONSTRAINT "project_tech_stack_techStackId_fkey" FOREIGN KEY ("techStackId") REFERENCES "tech_stack"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project_category" ADD CONSTRAINT "project_category_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project_category" ADD CONSTRAINT "project_category_categoryId_fkey" FOREIGN KEY ("categoryId") REFERENCES "Category"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Project" ADD CONSTRAINT "Project_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
