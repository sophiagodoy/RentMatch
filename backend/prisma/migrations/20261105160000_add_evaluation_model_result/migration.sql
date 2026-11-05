-- Preserva a versão, a faixa estimada e os avisos usados no resultado original.
ALTER TABLE "evaluations" ADD COLUMN "modelo" JSONB;
