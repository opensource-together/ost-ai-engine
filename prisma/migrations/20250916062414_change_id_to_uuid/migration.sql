/*
  Warnings:

  - The primary key for the `account` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The `id` column on the `account` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The primary key for the `session` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The `id` column on the `session` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The primary key for the `user` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The `id` column on the `user` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The primary key for the `user_social_link` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The `id` column on the `user_social_link` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - The primary key for the `verification` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The `id` column on the `verification` table would be dropped and recreated. This will lead to data loss if there is data in the column.
  - Changed the type of `userId` on the `account` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.
  - Changed the type of `userId` on the `session` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.
  - Changed the type of `userId` on the `user_social_link` table. No cast exists, the column would be dropped and recreated, which cannot be done if there is data, since the column is required.

*/
-- DropForeignKey
ALTER TABLE "public"."account" DROP CONSTRAINT "account_userId_fkey";

-- DropForeignKey
ALTER TABLE "public"."session" DROP CONSTRAINT "session_userId_fkey";

-- DropForeignKey
ALTER TABLE "public"."user_social_link" DROP CONSTRAINT "user_social_link_userId_fkey";

-- AlterTable
ALTER TABLE "public"."account" DROP CONSTRAINT "account_pkey",
DROP COLUMN "id",
ADD COLUMN     "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
DROP COLUMN "userId",
ADD COLUMN     "userId" UUID NOT NULL,
ADD CONSTRAINT "account_pkey" PRIMARY KEY ("id");

-- AlterTable
ALTER TABLE "public"."session" DROP CONSTRAINT "session_pkey",
DROP COLUMN "id",
ADD COLUMN     "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
DROP COLUMN "userId",
ADD COLUMN     "userId" UUID NOT NULL,
ADD CONSTRAINT "session_pkey" PRIMARY KEY ("id");

-- AlterTable
ALTER TABLE "public"."user" DROP CONSTRAINT "user_pkey",
DROP COLUMN "id",
ADD COLUMN     "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
ADD CONSTRAINT "user_pkey" PRIMARY KEY ("id");

-- AlterTable
ALTER TABLE "public"."user_social_link" DROP CONSTRAINT "user_social_link_pkey",
DROP COLUMN "id",
ADD COLUMN     "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
DROP COLUMN "userId",
ADD COLUMN     "userId" UUID NOT NULL,
ADD CONSTRAINT "user_social_link_pkey" PRIMARY KEY ("id");

-- AlterTable
ALTER TABLE "public"."verification" DROP CONSTRAINT "verification_pkey",
DROP COLUMN "id",
ADD COLUMN     "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
ADD CONSTRAINT "verification_pkey" PRIMARY KEY ("id");

-- CreateIndex
CREATE UNIQUE INDEX "user_social_link_userId_type_key" ON "public"."user_social_link"("userId", "type");

-- AddForeignKey
ALTER TABLE "public"."user_social_link" ADD CONSTRAINT "user_social_link_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."session" ADD CONSTRAINT "session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."account" ADD CONSTRAINT "account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
