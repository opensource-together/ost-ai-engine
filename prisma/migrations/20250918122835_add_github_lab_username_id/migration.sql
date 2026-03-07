/*
  Warnings:

  - A unique constraint covering the columns `[githubUsername]` on the table `user` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[gitlabUsername]` on the table `user` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[githubId]` on the table `user` will be added. If there are existing duplicate values, this will fail.
  - A unique constraint covering the columns `[gitlabId]` on the table `user` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "public"."user" ADD COLUMN     "githubId" TEXT,
ADD COLUMN     "githubUsername" TEXT,
ADD COLUMN     "gitlabId" TEXT,
ADD COLUMN     "gitlabUsername" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "user_githubUsername_key" ON "public"."user"("githubUsername");

-- CreateIndex
CREATE UNIQUE INDEX "user_gitlabUsername_key" ON "public"."user"("gitlabUsername");

-- CreateIndex
CREATE UNIQUE INDEX "user_githubId_key" ON "public"."user"("githubId");

-- CreateIndex
CREATE UNIQUE INDEX "user_gitlabId_key" ON "public"."user"("gitlabId");
