-- CreateTable
CREATE TABLE "public"."beta_signup" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "email" TEXT NOT NULL,

    CONSTRAINT "beta_signup_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "beta_signup_email_key" ON "public"."beta_signup"("email");
