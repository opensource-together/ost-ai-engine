-- Fix: rename verification_token back to verification (align with backend)
ALTER TABLE "public"."verification_token" RENAME TO "verification";
ALTER INDEX "verification_token_pkey" RENAME TO "verification_pkey";

-- Drop unused project_embedding table
ALTER TABLE "public"."project_embedding" DROP CONSTRAINT IF EXISTS "project_embedding_projectId_fkey";
DROP TABLE IF EXISTS "public"."project_embedding";

-- Create match tables (dbt-managed, but Prisma needs them for type generation)
-- Using IF NOT EXISTS so this is safe regardless of dbt run order.
CREATE TABLE IF NOT EXISTS "public"."match_global_recommendation" (
    "project_id" UUID NOT NULL,
    "stars" INTEGER,
    "last_synced_at" TIMESTAMP(3),

    CONSTRAINT "match_global_recommendation_pkey" PRIMARY KEY ("project_id")
);

CREATE TABLE IF NOT EXISTS "public"."match_user_recommendation" (
    "user_id" UUID NOT NULL,
    "project_id" UUID NOT NULL,
    "similarity_score" DOUBLE PRECISION,
    "preference_score" DOUBLE PRECISION,
    "freshness_score" DOUBLE PRECISION,
    "popularity_score" DOUBLE PRECISION,
    "final_score" DOUBLE PRECISION,
    "calculated_at" TIMESTAMP(3),

    CONSTRAINT "match_user_recommendation_pkey" PRIMARY KEY ("user_id", "project_id")
);
