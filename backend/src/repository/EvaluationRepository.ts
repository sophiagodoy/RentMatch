import { prisma } from "../lib/prisma.js";
import type { Prisma } from "../generated/prisma/client.js";
import type { EvaluationCreateDTO, EvaluationPrediction } from "../models/Evaluation.js";

const evaluationSelect = {
    id: true,
    bairro: true,
    tipo: true,
    areaM2: true,
    quartos: true,
    vagas: true,
    valorAnunciado: true,
    condominio: true,
    iptu: true,
    valorEstimado: true,
    classificacao: true,
    fatores: true,
    modelo: true,
    saved: true,
    createdAt: true
} satisfies Prisma.EvaluationSelect;

type EvaluationResult = Prisma.EvaluationGetPayload<{ select: typeof evaluationSelect }>;

function serializeEvaluation(evaluation: EvaluationResult) {
    return {
        ...evaluation,
        valorAnunciado: Number(evaluation.valorAnunciado),
        condominio: evaluation.condominio === null ? null : Number(evaluation.condominio),
        iptu: evaluation.iptu === null ? null : Number(evaluation.iptu),
        valorEstimado: Number(evaluation.valorEstimado)
    };
}

export class EvaluationRepository {
    async create(userId: string, data: EvaluationCreateDTO, result: EvaluationPrediction) {
        const evaluation = await prisma.evaluation.create({
            data: {
                userId,
                ...data,
                condominio: data.condominio ?? null,
                iptu: data.iptu ?? null,
                valorEstimado: result.valor_estimado,
                classificacao: result.classificacao,
                fatores: result.fatores,
                modelo: {
                    intervaloEstimado: result.intervalo_estimado,
                    valorBase: result.valor_base,
                    detalhe: result.detalhe,
                    avisos: result.avisos,
                    versao: result.versao_modelo
                }
            },
            select: evaluationSelect
        });
        return serializeEvaluation(evaluation);
    }

    async findHistory(userId: string, page: number, limit?: number) {
        const skip = limit === undefined ? undefined : (page - 1) * limit;
        const where = { userId, saved: true };

        const [evaluations, total, groupedClassifications] = await Promise.all([
            prisma.evaluation.findMany({
                where,
                orderBy: [{ createdAt: "desc" }, { id: "desc" }],
                ...(limit === undefined ? {} : { skip, take: limit }),
                select: evaluationSelect
            }),
            prisma.evaluation.count({ where }),
            prisma.evaluation.groupBy({
                by: ["classificacao"],
                where,
                _count: { _all: true }
            })
        ]);

        const countByClassification = Object.fromEntries(
            groupedClassifications.map(({ classificacao, _count }) => [classificacao, _count._all])
        );

        return {
            evaluations: evaluations.map(serializeEvaluation),
            total,
            countByClassification
        };
    }

    async findOwned(id: string, userId: string) {
        const evaluation = await prisma.evaluation.findFirst({
            where: { id, userId },
            select: evaluationSelect
        });

        return evaluation ? serializeEvaluation(evaluation) : null;
    }

    async saveOwned(id: string, userId: string) {
        // A propriedade é verificada na mesma operação que salva a avaliação.
        const [evaluation] = await prisma.evaluation.updateManyAndReturn({
            where: { id, userId },
            data: { saved: true },
            select: evaluationSelect
        });

        return evaluation ? serializeEvaluation(evaluation) : null;
    }

    async deleteOwned(id: string, userId: string) {
        // A condição de propriedade na própria exclusão evita apagar registros
        // de outro usuário e também evita uma janela entre consulta e exclusão.
        const result = await prisma.evaluation.deleteMany({
            where: { id, userId }
        });

        return result.count;
    }
}
