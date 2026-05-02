-- ProjectClassificationFailure DLQ (schema prisma `ProjectClassificationFailure`).
-- Intentionally no FK to public.Project (classifier may enqueue before sync).
-- Subsequent migration drops the FK if an older DDL path created it anyway.
CREATE TABLE IF NOT EXISTS "match"."project_classification_failure" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "projectId" UUID NOT NULL,
    "attempts" INTEGER NOT NULL DEFAULT 1,
    "lastError" TEXT NOT NULL,
    "lastAttemptAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "nextRetryAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "project_classification_failure_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "project_classification_failure_projectId_key" ON "match"."project_classification_failure"("projectId");

CREATE INDEX IF NOT EXISTS "project_classification_failure_nextRetryAt_idx" ON "match"."project_classification_failure"("nextRetryAt");
