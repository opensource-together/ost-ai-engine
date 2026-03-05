/*
  Warnings:

  - You are about to drop the column `githubUrl` on the `Project` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "public"."Project" DROP COLUMN "githubUrl",
ADD COLUMN     "keyfeatures" TEXT[],
ADD COLUMN     "projectGoals" TEXT[],
ADD COLUMN     "published" BOOLEAN NOT NULL DEFAULT false;
