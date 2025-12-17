/*
  Warnings:

  - A unique constraint covering the columns `[repoUrl]` on the table `Project` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Project_repoUrl_key" ON "public"."Project"("repoUrl");
