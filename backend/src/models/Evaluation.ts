import { z } from "zod";

const money = z.number().nonnegative().max(100_000).multipleOf(0.01);

export const EvaluationCreateSchema = z.object({
    bairro: z.string().trim().min(1, "Selecione o bairro.").max(120),
    tipo: z.enum(["Apartamento", "Casa", "Kitnet"]),
    areaM2: z.number().min(8, "A metragem mínima é 8 m².").max(2000),
    quartos: z.number().int().min(0).max(20),
    vagas: z.number().int().min(0).max(20),
    valorAnunciado: money.refine((value) => value > 0, "Informe um valor anunciado maior que zero."),
    condominio: money.nullish(),
    iptu: money.nullish()
});

export type EvaluationCreateDTO = z.infer<typeof EvaluationCreateSchema>;

export const EvaluationPredictionSchema = z.object({
    valor_estimado: z.number().positive().max(100_000_000).multipleOf(0.01),
    classificacao: z.enum(["Caro", "Preço Justo", "Oportunidade"]),
    fatores: z.array(z.object({
        fator: z.string(), descricao: z.string(),
        valor_informado: z.union([z.string(), z.number(), z.null()]),
        contribuicao_reais: z.number(), sentido: z.enum(["aumenta", "reduz", "neutro"])
    })),
    intervalo_estimado: z.tuple([z.number().nonnegative(), z.number().positive()]),
    valor_base: z.number(),
    detalhe: z.string(),
    avisos: z.array(z.string()),
    versao_modelo: z.string()
});

export type EvaluationPrediction = z.infer<typeof EvaluationPredictionSchema>;
