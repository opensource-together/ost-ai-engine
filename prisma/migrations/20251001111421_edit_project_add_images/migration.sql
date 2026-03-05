/*
  Warnings:

  - You are about to drop the column `image` on the `Project` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "public"."Project" DROP COLUMN "image",
ADD COLUMN     "imagesUrls" TEXT[],
ADD COLUMN     "logoUrl" TEXT;
