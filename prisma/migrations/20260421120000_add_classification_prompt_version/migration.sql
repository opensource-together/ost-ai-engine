-- Add prompt_version column to match.project_classification so every row can
-- be attributed to the exact prompt text (fingerprint) that produced it.
ALTER TABLE "match"."project_classification"
    ADD COLUMN IF NOT EXISTS "promptVersion" TEXT;
