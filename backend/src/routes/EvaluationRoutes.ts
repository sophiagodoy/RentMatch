import { Router, type Request, type Response } from "express";
import { evaluationController } from "../index.js";
import { authMiddleware } from "../middleware/AuthMiddleware.js";

const evaluationRoutes = Router();

evaluationRoutes.get(
    "/",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.list(req, res)
);

evaluationRoutes.delete(
    "/:id",
    authMiddleware,
    (req: Request, res: Response) => evaluationController.delete(req, res)
);

export { evaluationRoutes };
