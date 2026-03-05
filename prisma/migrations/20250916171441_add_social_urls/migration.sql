/*
  Warnings:

  - You are about to drop the `user_social_link` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "public"."user_social_link" DROP CONSTRAINT "user_social_link_userId_fkey";

-- AlterTable
ALTER TABLE "public"."user" ADD COLUMN     "discordUrl" TEXT,
ADD COLUMN     "githubUrl" TEXT,
ADD COLUMN     "linkedinUrl" TEXT,
ADD COLUMN     "twitterUrl" TEXT,
ADD COLUMN     "websiteUrl" TEXT;

-- DropTable
DROP TABLE "public"."user_social_link";

-- DropEnum
DROP TYPE "public"."SocialLinkType";
