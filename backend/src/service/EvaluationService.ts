import type { EvaluationRepository } from "../repository/EvaluationRepository.js";
import { AppError } from "../utils/AppError.js";

export class EvaluationService {
    constructor(private readonly evaluationRepository: EvaluationRepository) {}

    async list(userId: string, page = 1, limit?: number) {
        const result = await this.evaluationRepository.findHistory(userId, page, limit);
        const totalPages = limit === undefined
            ? (result.total === 0 ? 0 : 1)
            : Math.ceil(result.total / limit);

        return {
            data: result.evaluations,
            pagination: {
                page,
                limit: limit ?? null,
                total: result.total,
                totalPages,
                hasNext: limit !== undefined && page < totalPages,
                hasPrevious: limit !== undefined && page > 1 && totalPages > 0
            },
            summary: {
                total: result.total,
                caro: result.countByClassification["Caro"] ?? 0,
                precoJusto: result.countByClassification["Preço Justo"] ?? 0,
                oportunidade: result.countByClassification["Oportunidade"] ?? 0
            }
        };
    }

    async delete(userId: string, evaluationId: string) {
        const deletedCount = await this.evaluationRepository.deleteOwned(evaluationId, userId);

        if (deletedCount === 0) {
            // A mesma resposta cobre ID inexistente e avaliação de outra pessoa.
            throw new AppError("Avaliação não encontrada", 404);
        }
    }
}
