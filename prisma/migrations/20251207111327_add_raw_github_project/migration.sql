-- CreateTable
CREATE TABLE "raw_github_project" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "data" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "raw_github_project_pkey" PRIMARY KEY ("id")
);
