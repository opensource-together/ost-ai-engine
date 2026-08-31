-- CreateTable
CREATE TABLE "ml"."recommendation_ranker_model" (
    "id" UUID NOT NULL DEFAULT uuid_generate_v4(),
    "version" SERIAL NOT NULL,
    "coefficients" DOUBLE PRECISION[] NOT NULL,
    "intercept" DOUBLE PRECISION NOT NULL,
    "sampleCount" INTEGER NOT NULL,
    "positiveCount" INTEGER NOT NULL,
    "negativeCount" INTEGER NOT NULL,
    "precisionAt10" DOUBLE PRECISION NOT NULL,
    "recallAt10" DOUBLE PRECISION NOT NULL,
    "ndcgAt10" DOUBLE PRECISION NOT NULL,
    -- NDCG@10 of the static weighted blend on the same held-out sessions:
    -- the baseline this version had to beat to be persisted at all.
    "baselineNdcgAt10" DOUBLE PRECISION NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "recommendation_ranker_model_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "recommendation_ranker_model_coefficients_cardinality" CHECK (cardinality("coefficients") = 4),
    -- Postgres CHECK constraints cannot contain subqueries, so this indexes
    -- the 4 elements directly instead of unnest()-ing. Postgres treats NaN
    -- as equal to itself (unlike IEEE 754), so `= 'NaN'` reliably detects it;
    -- combined with the Infinity literals and a per-element NULL check, this
    -- rejects any malformed coefficient (including a too-short array, since
    -- out-of-bounds array indexing returns NULL).
    CONSTRAINT "recommendation_ranker_model_coefficients_finite" CHECK (
        "coefficients"[1] IS NOT NULL
        AND "coefficients"[1] NOT IN ('NaN'::double precision, 'Infinity'::double precision, '-Infinity'::double precision)
        AND "coefficients"[2] IS NOT NULL
        AND "coefficients"[2] NOT IN ('NaN'::double precision, 'Infinity'::double precision, '-Infinity'::double precision)
        AND "coefficients"[3] IS NOT NULL
        AND "coefficients"[3] NOT IN ('NaN'::double precision, 'Infinity'::double precision, '-Infinity'::double precision)
        AND "coefficients"[4] IS NOT NULL
        AND "coefficients"[4] NOT IN ('NaN'::double precision, 'Infinity'::double precision, '-Infinity'::double precision)
    ),
    -- Same finiteness guard as coefficients, applied to the scalar intercept.
    CONSTRAINT "recommendation_ranker_model_intercept_finite" CHECK (
        "intercept" NOT IN ('NaN'::double precision, 'Infinity'::double precision, '-Infinity'::double precision)
    )
);

-- CreateIndex
CREATE UNIQUE INDEX "recommendation_ranker_model_version_key" ON "ml"."recommendation_ranker_model"("version");

-- CreateIndex
CREATE INDEX "recommendation_ranker_model_createdAt_idx" ON "ml"."recommendation_ranker_model"("createdAt");
