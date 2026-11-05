-- Novas avaliações precisam ser salvas explicitamente.
ALTER TABLE "evaluations" ADD COLUMN "saved" BOOLEAN NOT NULL DEFAULT false;

-- Os registros anteriores já eram apresentados como salvos no histórico.
UPDATE "evaluations" SET "saved" = true;
