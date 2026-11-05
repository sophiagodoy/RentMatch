import { prisma } from "../lib/prisma.js";

export class EvaluationRepository {
    async findHistory(userId: string, page: number, limit?: number) {
        const skip = limit === undefined ? undefined : (page - 1) * limit;

        const [evaluations, total, groupedClassifications] = await Promise.all([
            prisma.evaluation.findMany({
                where: { userId },
                orderBy: [{ createdAt: "desc" }, { id: "desc" }],
                ...(limit === undefined ? {} : { skip, take: limit }),
                select: {
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
                    createdAt: true
                }
            }),
            prisma.evaluation.count({ where: { userId } }),
            prisma.evaluation.groupBy({
                by: ["classificacao"],
                where: { userId },
                _count: { _all: true }
            })
        ]);

        const countByClassification = Object.fromEntries(
            groupedClassifications.map(({ classificacao, _count }) => [classificacao, _count._all])
        );

        return {
            evaluations: evaluations.map((evaluation) => ({
                ...evaluation,
                valorAnunciado: Number(evaluation.valorAnunciado),
                condominio: evaluation.condominio === null ? null : Number(evaluation.condominio),
                iptu: evaluation.iptu === null ? null : Number(evaluation.iptu),
                valorEstimado: Number(evaluation.valorEstimado)
            })),
            total,
            countByClassification
        };
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
