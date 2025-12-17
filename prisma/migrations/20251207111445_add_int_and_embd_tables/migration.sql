-- CreateTable
CREATE TABLE "int_github_project" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "enrichedData" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "int_github_project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "embd_github_project" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "embeddingVector" vector(384) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "embd_github_project_pkey" PRIMARY KEY ("id")
);
