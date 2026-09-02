-- Append-only Mistral classifier usage (Grafana / Prometheus totals).
CREATE TABLE IF NOT EXISTS "match"."llm_usage" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "model" TEXT NOT NULL,
    "promptTokens" INTEGER NOT NULL,
    "completionTokens" INTEGER NOT NULL,
    "estimatedCostUsd" DOUBLE PRECISION NOT NULL,
    "requests" INTEGER NOT NULL,
    "http402" INTEGER NOT NULL DEFAULT 0,
    "http429" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "llm_usage_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "llm_usage_createdAt_idx" ON "match"."llm_usage"("createdAt");
