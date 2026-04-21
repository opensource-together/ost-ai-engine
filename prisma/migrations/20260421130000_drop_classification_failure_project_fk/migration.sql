-- Drop the FK from match.project_classification_failure -> public.Project.
--
-- The classifier runs BEFORE sync, so brand-new project IDs don't exist in
-- public.Project yet when a DLQ row is first written. Enforcing the FK caused
-- ForeignKeyViolation on batch DLQ writes, aborting the classifier's Output
-- and losing every successful classification in the same run.
--
-- The DLQ is a monitoring-only table. Referential integrity is not required
-- (and is actively harmful here) — dropping the constraint is the root-cause
-- fix; the in-app guard (isolated txn per DLQ row) remains as defense in depth.
ALTER TABLE "match"."project_classification_failure"
    DROP CONSTRAINT IF EXISTS "project_classification_failure_projectId_fkey";
