-- CreateTable
CREATE TABLE "evaluations" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "bairro" TEXT NOT NULL,
    "tipo" TEXT NOT NULL,
    "areaM2" DOUBLE PRECISION NOT NULL,
    "quartos" INTEGER NOT NULL,
    "vagas" INTEGER NOT NULL,
    "valorAnunciado" DECIMAL(12,2) NOT NULL,
    "condominio" DECIMAL(12,2),
    "iptu" DECIMAL(12,2),
    "valorEstimado" DECIMAL(12,2) NOT NULL,
    "classificacao" TEXT NOT NULL,
    "fatores" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "evaluations_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "evaluations_userId_createdAt_idx" ON "evaluations"("userId", "createdAt");

-- AddForeignKey
ALTER TABLE "evaluations" ADD CONSTRAINT "evaluations_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
