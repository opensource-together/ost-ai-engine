-- CreateEnum
CREATE TYPE "public"."TechStackType" AS ENUM ('TECH', 'LANGUAGE');

-- CreateTable
CREATE TABLE "public"."tech_stack" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "name" TEXT NOT NULL,
    "iconUrl" TEXT NOT NULL,
    "type" "public"."TechStackType" NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "tech_stack_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."user_tech_stack" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "userId" UUID NOT NULL,
    "techStackId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_tech_stack_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "tech_stack_name_key" ON "public"."tech_stack"("name");

-- CreateIndex
CREATE UNIQUE INDEX "user_tech_stack_userId_techStackId_key" ON "public"."user_tech_stack"("userId", "techStackId");

-- AddForeignKey
ALTER TABLE "public"."user_tech_stack" ADD CONSTRAINT "user_tech_stack_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."user_tech_stack" ADD CONSTRAINT "user_tech_stack_techStackId_fkey" FOREIGN KEY ("techStackId") REFERENCES "public"."tech_stack"("id") ON DELETE CASCADE ON UPDATE CASCADE;
