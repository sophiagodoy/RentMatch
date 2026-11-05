import { prisma } from "../lib/prisma.js";

export class EvaluationRepository {
    async deleteOwned(id: string, userId: string) {
        // A condição de propriedade na própria exclusão evita apagar registros
        // de outro usuário e também evita uma janela entre consulta e exclusão.
        const result = await prisma.evaluation.deleteMany({
            where: { id, userId }
        });

        return result.count;
    }
}
