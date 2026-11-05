import type { EvaluationRepository } from "../repository/EvaluationRepository.js";
import { AppError } from "../utils/AppError.js";

export class EvaluationService {
    constructor(private readonly evaluationRepository: EvaluationRepository) {}

    async delete(userId: string, evaluationId: string) {
        const deletedCount = await this.evaluationRepository.deleteOwned(evaluationId, userId);

        if (deletedCount === 0) {
            // A mesma resposta cobre ID inexistente e avaliação de outra pessoa.
            throw new AppError("Avaliação não encontrada", 404);
        }
    }
}
