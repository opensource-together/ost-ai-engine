-- CreateEnum
CREATE TYPE "public"."Provider" AS ENUM ('GITHUB', 'GITLAB');

-- CreateTable
CREATE TABLE "public"."project_tech_stack" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "techStackId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "project_tech_stack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."Project" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "title" TEXT NOT NULL,
    "description" TEXT,
    "repoUrl" TEXT,
    "provider" "public"."Provider" NOT NULL,
    "githubUrl" TEXT,
    "twitterUrl" TEXT,
    "linkedinUrl" TEXT,
    "discordUrl" TEXT,
    "websiteUrl" TEXT,
    "ownerId" UUID,
    "image" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "project_tech_stack_projectId_techStackId_key" ON "public"."project_tech_stack"("projectId", "techStackId");

-- AddForeignKey
ALTER TABLE "public"."project_tech_stack" ADD CONSTRAINT "project_tech_stack_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "public"."Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."project_tech_stack" ADD CONSTRAINT "project_tech_stack_techStackId_fkey" FOREIGN KEY ("techStackId") REFERENCES "public"."tech_stack"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Project" ADD CONSTRAINT "Project_ownerId_fkey" FOREIGN KEY ("ownerId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
