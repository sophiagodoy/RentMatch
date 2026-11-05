import type { Request, Response } from "express";
import { z } from "zod";
import type { EvaluationService } from "../service/EvaluationService.js";

const EvaluationIdSchema = z.uuid();

export class EvaluationController {
    constructor(private readonly evaluationService: EvaluationService) {}

    async delete(req: Request, res: Response) {
        const evaluationId = EvaluationIdSchema.parse(req.params.id);
        await this.evaluationService.delete(res.locals.userId, evaluationId);
        return res.status(204).send();
    }
}
