import type { Request, Response } from "express";
import { z } from "zod";
import type { EvaluationService } from "../service/EvaluationService.js";
import { EvaluationCreateSchema } from "../models/Evaluation.js";

const EvaluationIdSchema = z.uuid();
const EvaluationHistoryQuerySchema = z.object({
    limit: z.coerce.number().int().min(1).max(100).optional(),
    page: z.coerce.number().int().min(1).optional()
});

export class EvaluationController {
    constructor(private readonly evaluationService: EvaluationService) {}

    async create(req: Request, res: Response) {
        const data = EvaluationCreateSchema.parse(req.body);
        const evaluation = await this.evaluationService.create(res.locals.userId, data);
        return res.status(201).json(evaluation);
    }

    async getById(req: Request, res: Response) {
        const evaluationId = EvaluationIdSchema.parse(req.params.id);
        const evaluation = await this.evaluationService.getById(res.locals.userId, evaluationId);
        return res.status(200).json(evaluation);
    }

    async save(req: Request, res: Response) {
        const evaluationId = EvaluationIdSchema.parse(req.params.id);
        const evaluation = await this.evaluationService.save(res.locals.userId, evaluationId);
        return res.status(200).json(evaluation);
    }

    async list(req: Request, res: Response) {
        const query = EvaluationHistoryQuerySchema.parse(req.query);
        // Sem paginação explícita, a Home pode pedir ?limit=4 e "Ver todas"
        // pode omitir parâmetros para receber o histórico completo.
        const limit = query.limit ?? (query.page === undefined ? undefined : 20);
        const page = query.page ?? 1;
        const history = await this.evaluationService.list(res.locals.userId, page, limit);
        return res.status(200).json(history);
    }

    async delete(req: Request, res: Response) {
        const evaluationId = EvaluationIdSchema.parse(req.params.id);
        await this.evaluationService.delete(res.locals.userId, evaluationId);
        return res.status(204).send();
    }
}
