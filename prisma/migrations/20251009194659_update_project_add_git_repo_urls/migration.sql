/*
  Warnings:

  - You are about to drop the column `keyfeatures` on the `Project` table. All the data in the column will be lost.
  - You are about to drop the column `projectGoals` on the `Project` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "public"."Project" DROP COLUMN "keyfeatures",
DROP COLUMN "projectGoals",
ADD COLUMN     "githubUrl" TEXT,
ADD COLUMN     "gitlabUrl" TEXT;
