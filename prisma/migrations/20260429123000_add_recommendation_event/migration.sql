-- CreateEnum
CREATE TYPE "public"."RecommendationEventType" AS ENUM ('SHOWN', 'CLICKED', 'DISMISSED', 'STARRED_AFTER_RECO');

-- CreateEnum
CREATE TYPE "public"."RecommendationSource" AS ENUM ('PERSONALIZED', 'TRENDING', 'SIMILAR', 'SEMANTIC_SEARCH');

-- CreateTable
CREATE TABLE "public"."recommendation_event" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "userId" UUID NOT NULL,
    "projectId" UUID NOT NULL,
    "eventType" "public"."RecommendationEventType" NOT NULL,
    "source" "public"."RecommendationSource",
    "rank" INTEGER,
    "context" JSONB,
    "occurredAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "recommendation_event_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "recommendation_event_userId_projectId_idx" ON "public"."recommendation_event"("userId", "projectId");

-- CreateIndex
CREATE INDEX "recommendation_event_userId_occurredAt_idx" ON "public"."recommendation_event"("userId", "occurredAt");

-- CreateIndex
CREATE INDEX "recommendation_event_source_occurredAt_idx" ON "public"."recommendation_event"("source", "occurredAt");

-- AddForeignKey
ALTER TABLE "public"."recommendation_event" ADD CONSTRAINT "recommendation_event_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "public"."recommendation_event" ADD CONSTRAINT "recommendation_event_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "public"."Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
